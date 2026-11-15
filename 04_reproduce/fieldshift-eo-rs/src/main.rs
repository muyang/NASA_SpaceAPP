use fieldshift_eo_rs::*;
use std::{
    collections::BTreeMap,
    env, fs,
    io::{BufWriter, Write},
    path::Path,
};

fn rows(path: &Path, header: &str) -> Result<Vec<Vec<String>>, Box<dyn std::error::Error>> {
    let text = fs::read_to_string(path)?;
    let mut lines = text.lines();
    if lines.next() != Some(header) {
        return Err(format!("{}: unexpected schema", path.display()).into());
    }
    let mut out = vec![];
    for (i, l) in lines.enumerate() {
        if l.trim().is_empty() {
            continue;
        }
        let r: Vec<String> = l.split(',').map(str::to_string).collect();
        if r.len() != header.split(',').count() {
            return Err(format!("{} row {}: wrong field count", path.display(), i + 2).into());
        }
        out.push(r);
    }
    Ok(out)
}
#[derive(Default)]
struct Annual {
    rain: f64,
    runoff: f64,
    drain: f64,
    evap: f64,
    transp: f64,
    fert: f64,
    fix: f64,
    leach: f64,
    cover: f64,
    days: f64,
    stress: f64,
    cash_days: f64,
    yields: [f64; 3],
    werr: f64,
    cerr: f64,
    nerr: f64,
    forced: u32,
    missed: u32,
}
fn add(a: &mut Annual, d: &Daily) {
    let f = d.flux;
    a.rain += f.rain;
    a.runoff += f.runoff;
    a.drain += f.drainage;
    a.evap += f.evap;
    a.transp += f.transp;
    a.fert += f.fert;
    a.fix += f.fixation;
    a.leach += f.leach;
    a.cover += d.cover;
    a.days += 1.;
    a.stress += d.cash_stress_sum;
    a.cash_days += d.cash_days;
    a.werr = a.werr.max(d.water_error.abs());
    a.cerr = a.cerr.max(d.carbon_error.abs());
    a.nerr = a.nerr.max(d.nitrogen_error.abs());
}
fn has(s: &State, c: Species) -> bool {
    s.plants.iter().any(|p| p.species == c)
}
fn end(s: &mut State, c: Species, p: &[CropParam; 5], a: &mut Annual, ledger: &mut Flux) {
    let y = s.end_crop(c, p[c as usize], ledger);
    if c.cash() {
        a.yields[c as usize] += y;
    }
}
fn calendar_doy(year: i32, month: u32, day: u32) -> u32 {
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let m = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    m[..month as usize - 1].iter().sum::<u32>() + day
}
fn initial_organic(
    records: Vec<Vec<String>>,
    soils: &[Soil],
) -> Result<BTreeMap<String, Organic>, String> {
    let mut stocks = BTreeMap::new();
    for r in records {
        if r.len() != 3 || !soils.iter().any(|s| s.id == r[0]) {
            return Err("initial_soil: unknown soil or wrong field count".into());
        }
        let c: f64 = r[1].parse().map_err(|_| "invalid initial C")?;
        let n: f64 = r[2].parse().map_err(|_| "invalid initial N")?;
        if !c.is_finite() || !n.is_finite() || c <= 0. || n <= 0. {
            return Err("initial_soil: stocks must be finite and positive kg/ha".into());
        }
        if stocks.insert(r[0].clone(), Organic { c, n }).is_some() {
            return Err("initial_soil: duplicate soil".into());
        }
    }
    if stocks.len() != soils.len() {
        return Err("initial_soil: all soil IDs must be supplied".into());
    }
    Ok(stocks)
}
fn validate_atmosphere(records: &[Vec<String>], weather: &[Weather]) -> Result<Vec<f64>, String> {
    if records.len() != weather.len() {
        return Err("ET0 forcing must match every weather day".into());
    }
    let mut out = vec![];
    for (r, w) in records.iter().zip(weather.iter()) {
        if r.len() != 3 {
            return Err("ET0 schema".into());
        }
        let year: i32 = r[0].parse().map_err(|_| "ET0 year")?;
        let doy: u32 = r[1].parse().map_err(|_| "ET0 day")?;
        let value: f64 = r[2].parse().map_err(|_| "ET0 value")?;
        if year != w.year || doy != w.doy || !value.is_finite() || !(0.0..=25.0).contains(&value) {
            return Err("ET0 dates/units/ranges must match weather".into());
        }
        out.push(value);
    }
    Ok(out)
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3
        || args[3..].iter().any(|x| {
            ![
                "--calibration",
                "--legacy-roots",
                "--legacy-phenology",
                "--diagnostic-n-sufficient",
                "--use-reference-et",
                "--organic-mulch",
                "--dynamic-fixation",
            ]
            .contains(&x.as_str())
        })
    {
        return Err("usage: fieldshift-rs INPUT_DIR OUTPUT_DIR [--calibration] [--legacy-roots] [--legacy-phenology] [--diagnostic-n-sufficient]".into());
    }
    let calibration = args.iter().any(|x| x == "--calibration");
    let legacy = args.iter().any(|x| x == "--legacy-roots");
    let legacy_phenology = args.iter().any(|x| x == "--legacy-phenology");
    let diagnostic_n = args.iter().any(|x| x == "--diagnostic-n-sufficient");
    let reference_et = args.iter().any(|x| x == "--use-reference-et");
    let organic_mulch = args.iter().any(|x| x == "--organic-mulch");
    let dynamic_fixation = args.iter().any(|x| x == "--dynamic-fixation");
    if (reference_et || organic_mulch || dynamic_fixation) && !calibration {
        return Err(
            "experimental EO process options currently require --calibration (S0 baseline only)"
                .into(),
        );
    }
    let input = Path::new(&args[1]);
    let output = Path::new(&args[2]);
    fs::create_dir_all(output)?;
    let wr = rows(
        &input.join("weather.csv"),
        "year,doy,tmin_c,tmax_c,rain_mm,solar_MJ_m2",
    )?;
    let mut weather = vec![];
    for r in wr {
        let w = Weather {
            year: r[0].parse()?,
            doy: r[1].parse()?,
            tmin: r[2].parse()?,
            tmax: r[3].parse()?,
            rain: r[4].parse()?,
            rad: r[5].parse()?,
        };
        if !w.valid() {
            return Err("invalid weather".into());
        }
        weather.push(w);
    }
    if weather.is_empty() {
        return Err("empty weather".into());
    }
    for pair in weather.windows(2) {
        let a = pair[0];
        let b = pair[1];
        let year_days = calendar_doy(a.year, 12, 31);
        if !((a.year == b.year && b.doy == a.doy + 1)
            || (b.year == a.year + 1 && a.doy == year_days && b.doy == 1))
        {
            return Err("weather dates must be contiguous, unique and ordered".into());
        }
    }
    let first_year = weather[0].year;
    let last_year = weather.last().unwrap().year;
    if weather[0].doy != 1 || weather.last().unwrap().doy != calendar_doy(last_year, 12, 31) {
        return Err("full calendar years required".into());
    }
    let mut et0 = vec![];
    if reference_et {
        let records = rows(&input.join("atmosphere.csv"), "year,doy,reference_ET0_mm")?;
        et0 = validate_atmosphere(&records, &weather)?;
    }
    let mut soils = vec![];
    for r in rows(
        &input.join("soils.csv"),
        "soil_id,capacity_0_150_mm,capacity_150_450_mm,capacity_450_1000_mm",
    )? {
        let s = Soil {
            id: r[0].clone(),
            capacity: [r[1].parse()?, r[2].parse()?, r[3].parse()?],
        };
        if !s.valid() {
            return Err("invalid soil capacity".into());
        }
        soils.push(s);
    }
    if soils.is_empty() {
        return Err("no soils".into());
    }
    let initial_path = input.join("initial_soil.csv");
    let organic = if initial_path.exists() {
        Some(initial_organic(
            rows(&initial_path, "soil_id,SOM_C_kg_ha,SOM_N_kg_ha")?,
            &soils,
        )?)
    } else {
        None
    };
    let params=params_from_rows(&rows(&input.join("crops.csv"),"crop,base_C,optimum_C,ceiling_C,maturity_degday,rue_g_per_MJ_PAR,max_LAI,root_mm,harvest_index,N_fraction_at_1000kg,fixation_fraction,grain_N_fraction,N_dilution_exponent")?).map_err(|e|format!("crop schema: {e}"))?;
    let mut annual_file = BufWriter::new(fs::File::create(output.join("annual.csv"))?);
    writeln!(annual_file,"run_id,strategy,soil_id,initial_water_fraction,climate,parameter_multiplier,phase,year,cash_crop,corn_dry_kg_ha,soy_dry_kg_ha,oat_dry_kg_ha,rain_mm,runoff_mm,drainage_mm,evap_mm,transp_mm,fertilizer_N_kg_ha,fixation_N_kg_ha,leached_N_kg_ha,protective_cover_fraction,cash_water_stress_fraction,forced_harvests,missed_sowings,max_daily_water_error_mm,max_daily_C_error_kg_ha,max_daily_N_error_kg_ha")?;
    let mut daily_file = BufWriter::new(fs::File::create(output.join("representative_daily.csv"))?);
    let mut diagnostics = BufWriter::new(fs::File::create(output.join("crop_diagnostics.csv"))?);
    let mut canopy_file = BufWriter::new(fs::File::create(output.join("canopy_daily.csv"))?);
    writeln!(canopy_file,"year,doy,phase,crop,LAI_m2_m2,green_cover,protective_cover,available_water_mm,mineral_N_kg_ha,ET_mm,soil_evap_mm")?;
    writeln!(diagnostics,"run_id,strategy,soil_id,initial_water_fraction,climate,parameter_multiplier,phase,year,crop,sowing_doy,harvest_doy,growing_days,harvest_gdd,total_DM_kg_ha,plant_N_kg_ha,peak_LAI,intercepted_PAR_MJ_m2,radiation_potential_DM,temperature_potential_DM,water_potential_DM,actual_growth_DM,cold_loss_DM,N_limited_days,water_limited_days")?;
    writeln!(daily_file,"strategy,year,doy,available_water_mm,available_mineral_N_kg_ha,residue_C_kg_ha,SOM_C_kg_ha,protective_cover,rain_mm,runoff_mm,drainage_mm,evap_mm,transp_mm")?;
    let mut receipt = BufWriter::new(fs::File::create(output.join("balance_checks.csv"))?);
    writeln!(
        receipt,
        "run_id,water_residual_mm,carbon_residual_kg_ha,nitrogen_residual_kg_ha,passed"
    )?;
    let mut run_id = 0;
    let mut max_residual: f64 = 0.;
    for strategy in 0..3 {
        for soil in &soils {
            for initial in [0.4, 0.8] {
                for climate in 0..3 {
                    for mult in [0.85, 1., 1.15] {
                        for phase in 0..if strategy == 2 { 3 } else { 2 } {
                            if calibration && (strategy != 0 || climate != 0 || mult != 1.) {
                                continue;
                            }
                            run_id += 1;
                            let mut state = State::new(soil, initial);
                            state.partition_roots = !legacy;
                            state.photoperiod = !legacy_phenology;
                            state.organic_mulch = organic_mulch;
                            state.dynamic_fixation = dynamic_fixation;
                            if let Some(stocks) = &organic {
                                state.som = stocks[&soil.id];
                            }
                            let initial_stocks = (
                                state.water_total(),
                                state.carbon_total(),
                                state.nitrogen_total(),
                            );
                            let mut total = Flux::default();
                            let mut annual: BTreeMap<i32, Annual> = BTreeMap::new();
                            for (day_index, raw) in weather.iter().enumerate() {
                                state.reference_et0 = if reference_et {
                                    Some(et0[day_index])
                                } else {
                                    None
                                };
                                let mut w = *raw;
                                if climate == 1 {
                                    w.tmin += 2.;
                                    w.tmax += 2.;
                                    w.rain *= 0.8;
                                }
                                if climate == 2 {
                                    w.rain *= 1.2;
                                }
                                let a = annual.entry(w.year).or_default();
                                let cycle = (w.year - first_year + phase) as usize
                                    % if strategy == 2 { 3 } else { 2 };
                                let cash = if cycle == 0 {
                                    Species::Corn
                                } else if cycle == 1 {
                                    Species::Soy
                                } else {
                                    Species::Oat
                                };
                                // Fixed study dates, not local prescriptions. Clover persists over winter.
                                let mut management = Flux::default();
                                let mut fert = 0.;
                                if w.doy == calendar_doy(w.year, 4, 15) && cash == Species::Corn {
                                    end(&mut state, Species::Clover, &params, a, &mut management);
                                }
                                if w.doy == calendar_doy(w.year, 5, 1) {
                                    end(&mut state, Species::Rye, &params, a, &mut management);
                                }
                                let sow_day = match cash {
                                    Species::Corn => calendar_doy(w.year, 5, 1),
                                    Species::Soy => calendar_doy(w.year, 5, 15),
                                    _ => calendar_doy(w.year, 4, 1),
                                };
                                if w.doy == sow_day {
                                    if !state.plants.iter().any(|p| p.species.cash()) {
                                        state.sow(cash);
                                        if cash == Species::Corn {
                                            fert = 178.2;
                                        }
                                        if cash == Species::Oat {
                                            fert = 60.;
                                            state.sow(Species::Clover);
                                        }
                                        if diagnostic_n {
                                            fert += 2000.;
                                        }
                                    } else {
                                        a.missed += 1;
                                    }
                                }
                                if strategy == 1
                                    && cash == Species::Corn
                                    && w.doy == calendar_doy(w.year, 10, 20)
                                    && !has(&state, Species::Rye)
                                {
                                    state.sow(Species::Rye);
                                }
                                total.harvested_c += management.harvested_c;
                                total.harvested_n += management.harvested_n;
                                let d = step(&mut state, soil, w, &params, mult, mult, fert);
                                add(a, &d);
                                let f = d.flux;
                                if soil.id == soils[0].id
                                    && initial == 0.4
                                    && climate == 0
                                    && mult == 1.
                                {
                                    let (green, protective, lai) = state.cover(&params);
                                    let cash_lai = state
                                        .plants
                                        .iter()
                                        .zip(lai.iter())
                                        .filter(|(p, _)| p.species.cash())
                                        .map(|(_, v)| *v)
                                        .sum::<f64>();
                                    writeln!(canopy_file,"{},{},{phase},{},{cash_lai:.6},{green:.6},{protective:.6},{:.6},{:.6},{:.6},{:.6}",w.year,w.doy,cash.name(),state.water_total(),state.mineral_n+state.ammonium_n,f.evap+f.transp,f.evap)?;
                                }
                                total.rain += f.rain;
                                total.runoff += f.runoff;
                                total.drainage += f.drainage;
                                total.evap += f.evap;
                                total.transp += f.transp;
                                total.fert += f.fert;
                                total.fixation += f.fixation;
                                total.leach += f.leach;
                                total.growth_c += f.growth_c;
                                total.respired_c += f.respired_c;
                                let mature = state
                                    .plants
                                    .iter()
                                    .find(|p| p.species == cash)
                                    .map(|p| {
                                        p.progress(params[cash as usize], state.photoperiod) >= 1.
                                    })
                                    .unwrap_or(false);
                                let forced_date = if cash == Species::Oat {
                                    calendar_doy(w.year, 7, 31)
                                } else {
                                    calendar_doy(w.year, 10, 15)
                                };
                                if has(&state, cash) && (mature || w.doy >= forced_date) {
                                    let plant =
                                        state.plants.iter().find(|p| p.species == cash).unwrap();
                                    let q = plant.diagnostics;
                                    writeln!(diagnostics,"{run_id},S{strategy},{},{initial},{climate},{mult},{phase},{},{},{},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{},{}",soil.id,w.year,cash.name(),sow_day,w.doy,plant.age,plant.gdd,plant.dm,plant.n,q.peak_lai,q.par,q.radiation_potential,q.temperature_potential,q.water_potential,q.actual_growth,q.cold_loss,q.nitrogen_limited_days,q.water_limited_days)?;
                                    if !mature {
                                        a.forced += 1;
                                    }
                                    end(&mut state, cash, &params, a, &mut total);
                                }
                                if soil.id == soils[0].id
                                    && initial == 0.4
                                    && climate == 0
                                    && mult == 1.
                                    && phase == 0
                                {
                                    writeln!(daily_file,"S{strategy},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6}",w.year,w.doy,state.water_total(),state.mineral_n+state.ammonium_n,state.residue.c,state.som.c,d.cover,w.rain,f.runoff,f.drainage,f.evap,f.transp)?;
                                }
                                if state.water.iter().any(|x| *x < -1e-9)
                                    || state.mineral_n < -1e-8
                                    || state.ammonium_n < -1e-8
                                    || [state.carbon_total(), state.nitrogen_total()]
                                        .iter()
                                        .any(|x| !x.is_finite() || *x < 0.)
                                {
                                    return Err(format!("invalid stock in run {run_id}").into());
                                }
                            }
                            let we = initial_stocks.0 + total.rain
                                - total.runoff
                                - total.drainage
                                - total.evap
                                - total.transp
                                - state.water_total();
                            let ce = initial_stocks.1 + total.growth_c
                                - total.harvested_c
                                - total.respired_c
                                - state.carbon_total();
                            let ne = initial_stocks.2 + total.fert + total.fixation
                                - total.harvested_n
                                - total.leach
                                - state.nitrogen_total();
                            let passed = we.abs() < 1e-6 && ce.abs() < 1e-5 && ne.abs() < 1e-6;
                            max_residual = max_residual.max(we.abs()).max(ce.abs()).max(ne.abs());
                            writeln!(receipt, "{run_id},{we:.12},{ce:.12},{ne:.12},{passed}")?;
                            if !passed {
                                return Err(format!("mass balance failed in run {run_id}").into());
                            }
                            let climate_name =
                                ["historical", "hot_dry_perturbation", "wet_perturbation"][climate];
                            for (year, a) in annual {
                                let cycle = (year - first_year + phase) as usize
                                    % if strategy == 2 { 3 } else { 2 };
                                let crop = ["corn", "soy", "oat"][cycle];
                                let stress = if a.cash_days > 0. {
                                    a.stress / a.cash_days
                                } else {
                                    0.
                                };
                                writeln!(annual_file,"{run_id},S{strategy},{},{initial},{climate_name},{mult},{phase},{year},{crop},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{stress:.6},{},{},{:.12},{:.12},{:.12}",soil.id,a.yields[0],a.yields[1],a.yields[2],a.rain,a.runoff,a.drain,a.evap,a.transp,a.fert,a.fix,a.leach,a.cover/a.days,a.forced,a.missed,a.werr,a.cerr,a.nerr)?;
                            }
                        }
                    }
                }
            }
        }
    }
    annual_file.flush()?;
    daily_file.flush()?;
    diagnostics.flush()?;
    canopy_file.flush()?;
    receipt.flush()?;
    let version = env!("CARGO_PKG_VERSION");
    let root_partition = !legacy;
    let corrected_phenology = !legacy_phenology;
    let custom_initial_stocks = organic.is_some();
    fs::write(output.join("execution_summary.json"),format!("{{\"engine\":\"fieldshift-rs {version} independent reduced model\",\"APSIM_executed\":false,\"root_partition\":{root_partition},\"corrected_phenology\":{corrected_phenology},\"custom_initial_stocks\":{custom_initial_stocks},\"diagnostic_N_excess\":{diagnostic_n},\"runs\":{run_id},\"weather_days_per_run\":{},\"first_year\":{first_year},\"last_year\":{last_year},\"max_absolute_balance_residual\":{max_residual},\"all_mass_balances_passed\":true}}\n",weather.len()))?;
    fs::write(output.join("process_options.json"),format!("{{\"experimental_engine\":\"fieldshift-eo-rs 0.3.0\",\"reference_ET0\":{reference_et},\"FAO56_organic_mulch_approximation\":{organic_mulch},\"deficit_limited_dynamic_fixation\":{dynamic_fixation},\"recommended_for_field_use\":false}}\n"))?;
    println!(
        "Completed {run_id} independent Rust-model runs; all water/C/N balance checks passed."
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn leap_calendar() {
        assert_eq!(calendar_doy(2020, 12, 31), 366);
        assert_eq!(calendar_doy(2019, 12, 31), 365);
        assert_eq!(calendar_doy(2020, 5, 1), 122);
    }
    #[test]
    fn atmospheric_dates_units_and_completeness_are_required() {
        let weather = vec![Weather {
            year: 2020,
            doy: 1,
            tmin: 0.,
            tmax: 10.,
            rain: 0.,
            rad: 10.,
        }];
        let record = |d: &str, v: &str| vec![vec!["2020".into(), d.into(), v.into()]];
        assert_eq!(
            validate_atmosphere(&record("1", "3.5"), &weather).unwrap(),
            vec![3.5]
        );
        assert!(validate_atmosphere(&[], &weather).is_err());
        for value in ["NaN", "-1", "26"] {
            assert!(validate_atmosphere(&record("1", value), &weather).is_err());
        }
        assert!(validate_atmosphere(&record("2", "3.5"), &weather).is_err());
    }
    #[test]
    fn initial_stocks_require_complete_unique_finite_values() {
        let soils = vec![Soil {
            id: "s".into(),
            capacity: [10.; 3],
        }];
        let record = |c: &str| vec![vec!["s".into(), c.into(), "1000".into()]];
        assert_eq!(
            initial_organic(record("12000"), &soils).unwrap()["s"].c,
            12000.
        );
        for bad in ["NaN", "inf", "-1", "0"] {
            assert!(initial_organic(record(bad), &soils).is_err());
        }
        assert!(initial_organic(vec![], &soils).is_err());
        assert!(initial_organic(vec![record("12000")[0].clone(); 2], &soils).is_err());
    }
}
