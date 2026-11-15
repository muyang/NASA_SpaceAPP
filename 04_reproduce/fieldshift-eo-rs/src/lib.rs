//! Independent reduced process model. No APSIM source code is incorporated.
//! Units: mm water, kg dry matter/C/N per hectare, degrees Celsius, MJ/m2/day.
use std::collections::BTreeMap;
pub const C_FRAC: f64 = 0.45;

/// Approximate FAO56 organic-residue rule, not a calibrated residue-cover model.
pub fn organic_mulch_attenuation(cover: f64) -> f64 {
    1. - 0.5 * cover.clamp(0., 1.)
}

/// Exploratory phenology/water-dependent ceiling; soil N is used before fixation.
/// Coefficients are disclosed priors, not an estimate of seasonal field Ndfa.
pub fn fixation_capacity(need: f64, max_fraction: f64, progress: f64, water: f64) -> f64 {
    let activation = (progress / 0.2).clamp(0., 1.);
    let decline = ((1.05 - progress) / 0.2).clamp(0., 1.);
    need * max_fraction * activation * decline * water.clamp(0., 1.)
}

#[derive(Clone, Copy, Debug)]
pub struct Weather {
    pub year: i32,
    pub doy: u32,
    pub tmin: f64,
    pub tmax: f64,
    pub rain: f64,
    pub rad: f64,
}
impl Weather {
    pub fn valid(&self) -> bool {
        self.doy > 0
            && self.doy <= 366
            && [self.tmin, self.tmax, self.rain, self.rad]
                .iter()
                .all(|x| x.is_finite())
            && self.tmax >= self.tmin
            && self.rain >= 0.
            && self.rad >= 0.
    }
    pub fn mean(&self) -> f64 {
        (self.tmin + self.tmax) / 2.
    }
}
#[derive(Clone, Debug)]
pub struct Soil {
    pub id: String,
    pub capacity: [f64; 3],
}
impl Soil {
    pub fn valid(&self) -> bool {
        self.capacity.iter().all(|x| x.is_finite() && *x > 0.)
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Species {
    Corn,
    Soy,
    Oat,
    Rye,
    Clover,
}
impl Species {
    pub fn name(self) -> &'static str {
        match self {
            Self::Corn => "corn",
            Self::Soy => "soy",
            Self::Oat => "oat",
            Self::Rye => "rye",
            Self::Clover => "clover",
        }
    }
    pub fn cash(self) -> bool {
        matches!(self, Self::Corn | Self::Soy | Self::Oat)
    }
}
#[derive(Clone, Copy, Debug)]
pub struct CropParam {
    pub base: f64,
    pub optimum: f64,
    pub ceiling: f64,
    pub maturity: f64,
    pub rue: f64,
    pub max_lai: f64,
    pub root_mm: f64,
    pub hi: f64,
    pub n_frac: f64,
    pub fixation: f64,
    pub grain_n: f64,
    pub n_dilution: f64,
}
impl CropParam {
    pub fn valid(&self) -> bool {
        [
            self.base,
            self.optimum,
            self.ceiling,
            self.maturity,
            self.rue,
            self.max_lai,
            self.root_mm,
            self.hi,
            self.n_frac,
            self.fixation,
            self.grain_n,
            self.n_dilution,
        ]
        .iter()
        .all(|x| x.is_finite())
            && self.base < self.optimum
            && self.optimum < self.ceiling
            && self.maturity > 0.
            && self.rue > 0.
            && self.max_lai > 0.
            && self.root_mm > 0.
            && self.root_mm <= 1000.
            && (0.0..=1.0).contains(&self.hi)
            && (0.0..=1.0).contains(&self.fixation)
            && self.n_frac > 0.
            && self.n_frac <= 1.
            && self.grain_n >= 0.
            && self.grain_n <= 1.
            && (0.0..1.0).contains(&self.n_dilution)
    }
    pub fn critical_n(&self, dm: f64) -> f64 {
        dm * self.n_frac * ((dm / 1000.).max(1.).powf(-self.n_dilution)).max(0.1)
    }
}
#[derive(Clone, Debug)]
pub struct Plant {
    pub species: Species,
    pub dm: f64,
    pub n: f64,
    pub gdd: f64,
    pub age: u32,
    pub anthesis_age: Option<u32>,
    pub diagnostics: GrowthDiagnostics,
}
#[derive(Clone, Copy, Debug, Default)]
pub struct GrowthDiagnostics {
    pub par: f64,
    pub radiation_potential: f64,
    pub temperature_potential: f64,
    pub water_potential: f64,
    pub actual_growth: f64,
    pub cold_loss: f64,
    pub peak_lai: f64,
    pub nitrogen_limited_days: u32,
    pub water_limited_days: u32,
}
impl Plant {
    pub fn progress(&self, param: CropParam, corrected: bool) -> f64 {
        if corrected && self.species == Species::Corn {
            if let Some(start) = self.anthesis_age {
                0.5 + 0.5 * (self.age - start) as f64 / 60.
            } else {
                0.5 * self.gdd / (param.maturity * 0.5)
            }
        } else {
            self.gdd / param.maturity
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct Organic {
    pub c: f64,
    pub n: f64,
}
#[derive(Clone, Copy, Debug, Default)]
pub struct Flux {
    pub rain: f64,
    pub runoff: f64,
    pub drainage: f64,
    pub evap: f64,
    pub transp: f64,
    pub fert: f64,
    pub fixation: f64,
    pub leach: f64,
    pub growth_c: f64,
    pub harvested_c: f64,
    pub harvested_n: f64,
    pub respired_c: f64,
}
#[derive(Clone, Debug)]
pub struct State {
    pub water: [f64; 3],
    pub mineral_n: f64,
    pub ammonium_n: f64,
    pub som: Organic,
    pub residue: Organic,
    pub root_residue: Organic,
    pub partition_roots: bool,
    pub photoperiod: bool,
    pub reference_et0: Option<f64>,
    pub organic_mulch: bool,
    pub dynamic_fixation: bool,
    pub latitude: f64,
    pub soy_critical_daylength: f64,
    pub soy_photoperiod_sensitivity: f64,
    pub plants: Vec<Plant>,
}
impl State {
    pub fn new(soil: &Soil, fraction: f64) -> Self {
        assert!(soil.valid() && (0.0..=1.0).contains(&fraction));
        Self {
            water: soil.capacity.map(|x| x * fraction),
            mineral_n: 50.,
            ammonium_n: 0.,
            som: Organic {
                c: 30000.,
                n: 2500.,
            },
            residue: Organic { c: 1000., n: 15. },
            root_residue: Organic { c: 0., n: 0. },
            partition_roots: true,
            photoperiod: true,
            reference_et0: None,
            organic_mulch: false,
            dynamic_fixation: false,
            latitude: 42.04,
            soy_critical_daylength: 14.,
            soy_photoperiod_sensitivity: 0.2,
            plants: vec![],
        }
    }
    pub fn water_total(&self) -> f64 {
        self.water.iter().sum()
    }
    pub fn carbon_total(&self) -> f64 {
        self.som.c
            + self.residue.c
            + self.root_residue.c
            + self.plants.iter().map(|p| p.dm * C_FRAC).sum::<f64>()
    }
    pub fn nitrogen_total(&self) -> f64 {
        self.mineral_n
            + self.ammonium_n
            + self.som.n
            + self.residue.n
            + self.root_residue.n
            + self.plants.iter().map(|p| p.n).sum::<f64>()
    }
    pub fn sow(&mut self, species: Species) {
        assert!(!self.plants.iter().any(|p| p.species == species));
        self.plants.push(Plant {
            species,
            dm: 0.,
            n: 0.,
            gdd: 0.,
            age: 0,
            anthesis_age: None,
            diagnostics: GrowthDiagnostics::default(),
        });
    }
    /// Harvest grain only for cash crops; remaining biomass/N stays within residue.
    pub fn end_crop(&mut self, species: Species, param: CropParam, flux: &mut Flux) -> f64 {
        let Some(i) = self.plants.iter().position(|p| p.species == species) else {
            return 0.;
        };
        let plant = self.plants.remove(i);
        let progress = plant.progress(param, self.photoperiod);
        let grainfill = ((progress - 0.45) / 0.55).clamp(0., 1.);
        let yield_dm = if species.cash() {
            plant.dm * 0.8 * param.hi * grainfill
        } else {
            0.
        };
        let root_dm = if self.partition_roots {
            plant.dm * 0.2
        } else {
            0.
        };
        let root_n = if self.partition_roots {
            plant.n * 0.2
        } else {
            0.
        };
        let grain_n = (yield_dm * param.grain_n).min(plant.n - root_n);
        flux.harvested_c += yield_dm * C_FRAC;
        flux.harvested_n += grain_n;
        self.residue.c += (plant.dm - root_dm - yield_dm) * C_FRAC;
        self.residue.n += plant.n - root_n - grain_n;
        self.root_residue.c += root_dm * C_FRAC;
        self.root_residue.n += root_n;
        yield_dm
    }
    pub fn cover(&self, params: &[CropParam; 5]) -> (f64, f64, Vec<f64>) {
        let lai: Vec<f64> = self
            .plants
            .iter()
            .map(|p| {
                let cp = params[p.species as usize];
                let stage = p.progress(cp, self.photoperiod);
                let senescence = if p.species.cash() {
                    ((1. - stage) / 0.3).clamp(0., 1.)
                } else {
                    1.
                };
                let leaf_coefficient = 0.001625 - 0.001 * (stage / 0.8).clamp(0., 1.);
                ((0.03 + p.dm * leaf_coefficient).min(cp.max_lai) * senescence).max(0.)
            })
            .collect();
        let green = 1. - (-0.6 * lai.iter().sum::<f64>()).exp();
        let residue_cover = 1. - (-(self.residue.c / C_FRAC) / 2500.).exp();
        (green, 1. - (1. - green) * (1. - residue_cover), lai)
    }
}

/// Curve-number screening runoff, mm/day. Daily rainfall is treated as an event.
pub fn runoff(rain: f64, cover: f64) -> f64 {
    let cn = 75. - 12. * cover.clamp(0., 1.);
    let s = 25400. / cn - 254.;
    if rain <= 0.2 * s {
        0.
    } else {
        (rain - 0.2 * s).powi(2) / (rain + 0.8 * s)
    }
}
/// Available-water buckets: capacity is SSURGO AWC x thickness, not SAT or DUL.
pub fn infiltrate(state: &mut State, soil: &Soil, rain: f64, cover: f64, flux: &mut Flux) {
    flux.rain += rain;
    let q = runoff(rain, cover);
    flux.runoff += q;
    let mut incoming = rain - q;
    for i in 0..3 {
        let total = state.water[i] + incoming;
        state.water[i] = total.min(soil.capacity[i]);
        incoming = (total - soil.capacity[i]).max(0.);
    }
    flux.drainage += incoming;
}
pub fn temperature_factor(t: f64, p: CropParam) -> f64 {
    if t <= p.base || t >= p.ceiling {
        0.
    } else if t <= p.optimum {
        (t - p.base) / (p.optimum - p.base)
    } else {
        (p.ceiling - t) / (p.ceiling - p.optimum)
    }
}
/// Simultaneous layer allocation, invariant to plant ordering; no overdraw.
pub fn daylength(latitude: f64, doy: u32) -> f64 {
    let declination = 0.409 * (2. * std::f64::consts::PI * doy as f64 / 365. - 1.39).sin();
    let omega = (-latitude.to_radians().tan() * declination.tan())
        .clamp(-1., 1.)
        .acos();
    24. * omega / std::f64::consts::PI
}
pub fn development_factor(
    species: Species,
    day_hours: f64,
    critical: f64,
    sensitivity: f64,
) -> f64 {
    if species == Species::Soy {
        (1. - sensitivity * (day_hours - critical).max(0.)).clamp(0.4, 1.)
    } else {
        1.
    }
}
pub fn allocate_water(water: &mut [f64; 3], demands: &[f64], roots: &[f64]) -> Vec<f64> {
    assert_eq!(demands.len(), roots.len());
    let mut req = vec![[0.; 3]; demands.len()];
    let top = [0., 150., 450.];
    let bottom = [150., 450., 1000.];
    for i in 0..demands.len() {
        let access: [f64; 3] = std::array::from_fn(|j| {
            ((roots[i] - top[j]) / (bottom[j] - top[j])).clamp(0., 1.) * water[j]
        });
        let total = access.iter().sum::<f64>();
        if total > 0. {
            for j in 0..3 {
                req[i][j] = demands[i] * access[j] / total;
            }
        }
    }
    let mut actual = vec![0.; demands.len()];
    for j in 0..3 {
        let total = req.iter().map(|r| r[j]).sum::<f64>();
        let scale = if total > 0. {
            (water[j] / total).min(1.)
        } else {
            0.
        };
        let used = total * scale;
        water[j] = (water[j] - used).max(0.);
        for i in 0..demands.len() {
            actual[i] += req[i][j] * scale;
        }
    }
    actual
}

pub fn decompose(state: &mut State, temp: f64, moisture: f64, k_factor: f64, flux: &mut Flux) {
    let env = ((temp - 0.) / 25.).clamp(0., 2.) * moisture.clamp(0., 1.);
    let som_f = (0.00002 * k_factor * env).min(1.);
    let sc = state.som.c * som_f;
    let sn = state.som.n * som_f;
    state.som.c -= sc;
    state.som.n -= sn;
    state.ammonium_n += sn;
    flux.respired_c += sc;
    decompose_residue(
        &mut state.residue,
        &mut state.som,
        &mut state.mineral_n,
        &mut state.ammonium_n,
        k_factor,
        env,
        flux,
    );
    decompose_residue(
        &mut state.root_residue,
        &mut state.som,
        &mut state.mineral_n,
        &mut state.ammonium_n,
        k_factor,
        env,
        flux,
    );
}
fn decompose_residue(
    residue: &mut Organic,
    som: &mut Organic,
    nitrate: &mut f64,
    ammonium: &mut f64,
    k_factor: f64,
    env: f64,
    flux: &mut Flux,
) {
    let mut f = (0.002 * k_factor * env).min(1.);
    let need_per_fraction = residue.c * 0.2 / 12. - residue.n;
    if need_per_fraction > 0. {
        f = f.min((*nitrate + *ammonium) / need_per_fraction);
    }
    let c = residue.c * f;
    let n = residue.n * f;
    let hum_c = c * 0.2;
    let hum_n = hum_c / 12.;
    residue.c -= c;
    residue.n -= n;
    som.c += hum_c;
    som.n += hum_n;
    if n >= hum_n {
        *ammonium += n - hum_n;
    } else {
        let take = (hum_n - n).min(*nitrate);
        *nitrate -= take;
        *ammonium -= hum_n - n - take;
    }
    flux.respired_c += c - hum_c;
    if nitrate.abs() < 1e-12 {
        *nitrate = 0.;
    }
    if ammonium.abs() < 1e-12 {
        *ammonium = 0.;
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct Daily {
    pub flux: Flux,
    pub cover: f64,
    pub cash_stress_sum: f64,
    pub cash_days: f64,
    pub water_error: f64,
    pub carbon_error: f64,
    pub nitrogen_error: f64,
}

pub fn step(
    state: &mut State,
    soil: &Soil,
    w: Weather,
    params: &[CropParam; 5],
    rue_factor: f64,
    k_factor: f64,
    fert: f64,
) -> Daily {
    assert!(w.valid() && soil.valid());
    assert!(fert >= 0. && rue_factor > 0. && k_factor > 0.);
    let before = (
        state.water_total(),
        state.carbon_total(),
        state.nitrogen_total(),
    );
    let mut flux = Flux::default();
    let (green, protective, lai) = state.cover(params);
    infiltrate(state, soil, w.rain, protective, &mut flux);
    // Assumed UAN-like partition after rapid hydrolysis, not a farm record.
    state.mineral_n += fert * 0.25;
    state.ammonium_n += fert * 0.75;
    flux.fert += fert;
    let moisture = state.water_total() / soil.capacity.iter().sum::<f64>();
    decompose(state, w.mean(), moisture, k_factor, &mut flux);
    let nitrified =
        state.ammonium_n * (0.06 * ((w.mean() + 5.) / 30.).clamp(0., 1.5) * moisture).clamp(0., 1.);
    state.ammonium_n -= nitrified;
    state.mineral_n += nitrified;
    let leach_fraction = if flux.drainage > 0. {
        (0.8 * flux.drainage / (state.water_total() + flux.drainage)).clamp(0., 1.)
    } else {
        0.
    };
    flux.leach = state.mineral_n * leach_fraction;
    state.mineral_n -= flux.leach;
    // Radiation-based ET demand proxy, not FAO reference ET or APSIM SoilWat.
    let pet = state.reference_et0.unwrap_or_else(|| {
        (0.75 * w.rad / 2.45 * ((w.mean() + 5.) / (w.mean() + 20.).max(1.)).clamp(0., 1.)).max(0.)
    });
    assert!(pet.is_finite() && pet >= 0.);
    let attenuation = if state.organic_mulch {
        organic_mulch_attenuation(1. - (-(state.residue.c / C_FRAC) / 2500.).exp())
    } else {
        (-0.0003 * state.residue.c / C_FRAC).exp()
    };
    let e_demand = pet * (1. - green) * attenuation;
    flux.evap = e_demand.min(state.water[0]);
    state.water[0] -= flux.evap;
    let weights: Vec<f64> = state
        .plants
        .iter()
        .zip(lai.iter())
        .map(|(p, l)| {
            l * if p.species == Species::Clover {
                0.5
            } else {
                1.
            }
        })
        .collect();
    let sum = weights.iter().sum::<f64>();
    let shares: Vec<f64> = weights
        .iter()
        .map(|x| if sum > 0. { x / sum } else { 0. })
        .collect();
    let demands: Vec<f64> = shares.iter().map(|x| pet * green * x).collect();
    let roots: Vec<f64> = state
        .plants
        .iter()
        .map(|p| {
            let cp = params[p.species as usize];
            (150. + cp.root_mm * (p.gdd / (0.5 * cp.maturity).min(700.)).clamp(0., 1.))
                .min(cp.root_mm)
        })
        .collect();
    let actual = allocate_water(&mut state.water, &demands, &roots);
    flux.transp = actual.iter().sum();
    let mut potential = vec![0.; state.plants.len()];
    let mut temperature_potential = vec![0.; state.plants.len()];
    let mut radiation_potential = vec![0.; state.plants.len()];
    let mut fixed = vec![0.; state.plants.len()];
    let mut needs = vec![0.; state.plants.len()];
    let mut cash_stress_sum = 0.;
    let mut cash_days = 0.;
    for i in 0..state.plants.len() {
        let p = &state.plants[i];
        let cp = params[p.species as usize];
        let stress = if demands[i] > 1e-9 {
            (actual[i] / demands[i]).clamp(0., 1.)
        } else {
            1.
        };
        radiation_potential[i] = w.rad * 0.48 * green * shares[i] * cp.rue * rue_factor * 10.;
        temperature_potential[i] = radiation_potential[i] * temperature_factor(w.mean(), cp);
        potential[i] = temperature_potential[i] * stress;
        let need = (cp.critical_n(p.dm + potential[i]) - p.n).max(0.);
        if state.dynamic_fixation {
            fixed[i] =
                fixation_capacity(need, cp.fixation, p.progress(cp, state.photoperiod), stress);
            needs[i] = need;
        } else {
            fixed[i] = need * cp.fixation;
            needs[i] = need - fixed[i];
        }
        if p.species.cash() {
            cash_stress_sum += 1. - stress;
            cash_days += 1.;
        }
    }
    let total_need = needs.iter().sum::<f64>();
    let scale = if total_need > 0. {
        ((state.mineral_n + state.ammonium_n) / total_need).min(1.)
    } else {
        0.
    };
    for i in 0..state.plants.len() {
        let p = &mut state.plants[i];
        let cp = params[p.species as usize];
        let uptake = needs[i] * scale;
        let fixation = if state.dynamic_fixation {
            fixed[i].min((needs[i] - uptake).max(0.))
        } else {
            fixed[i]
        };
        let n = uptake + fixation;
        let available = p.n + n;
        let mut lo = 0.;
        let mut hi = potential[i];
        if cp.critical_n(p.dm + hi) > available {
            for _ in 0..40 {
                let mid = (lo + hi) / 2.;
                if cp.critical_n(p.dm + mid) <= available {
                    lo = mid
                } else {
                    hi = mid
                }
            }
        } else {
            lo = hi;
        }
        let growth = lo;
        p.diagnostics.par += w.rad * 0.48 * green * shares[i];
        p.diagnostics.radiation_potential += radiation_potential[i];
        p.diagnostics.temperature_potential += temperature_potential[i];
        p.diagnostics.water_potential += potential[i];
        p.diagnostics.actual_growth += growth;
        p.diagnostics.peak_lai = p.diagnostics.peak_lai.max(lai[i]);
        if growth < potential[i] * 0.99 && potential[i] > 1e-6 {
            p.diagnostics.nitrogen_limited_days += 1;
        }
        if potential[i] < temperature_potential[i] * 0.99 && temperature_potential[i] > 1e-6 {
            p.diagnostics.water_limited_days += 1;
        }
        let nitrate_uptake = uptake.min(state.mineral_n);
        state.mineral_n -= nitrate_uptake;
        state.ammonium_n -= uptake - nitrate_uptake;
        flux.fixation += fixation;
        flux.growth_c += growth * C_FRAC;
        p.dm += growth;
        p.n += n;
        let photoperiod_factor = if state.photoperiod {
            development_factor(
                p.species,
                daylength(state.latitude, w.doy),
                state.soy_critical_daylength,
                state.soy_photoperiod_sensitivity,
            )
        } else {
            1.
        };
        p.gdd += (w.mean() - cp.base).max(0.) * photoperiod_factor;
        p.age += 1;
        if state.photoperiod
            && p.species == Species::Corn
            && p.anthesis_age.is_none()
            && p.gdd >= cp.maturity * 0.5
        {
            p.anthesis_age = Some(p.age);
        }
        // Modest cold senescence is transferred to residue, not lost from balances.
        if w.mean() < 0. {
            let f = 0.01;
            let dm = p.dm * f;
            let pn = p.n * f;
            p.dm -= dm;
            p.n -= pn;
            p.diagnostics.cold_loss += dm;
            let root_fraction = if state.partition_roots { 0.2 } else { 0. };
            state.residue.c += dm * C_FRAC * (1. - root_fraction);
            state.residue.n += pn * (1. - root_fraction);
            state.root_residue.c += dm * C_FRAC * root_fraction;
            state.root_residue.n += pn * root_fraction;
        }
    }
    Daily {
        flux,
        cover: protective,
        cash_stress_sum,
        cash_days,
        water_error: state.water_total() - before.0 - flux.rain
            + flux.runoff
            + flux.drainage
            + flux.evap
            + flux.transp,
        carbon_error: state.carbon_total() - before.1 - flux.growth_c + flux.respired_c,
        nitrogen_error: state.nitrogen_total() - before.2 - flux.fert - flux.fixation + flux.leach,
    }
}

pub fn params_from_rows(rows: &[Vec<String>]) -> Result<[CropParam; 5], String> {
    let mut map = BTreeMap::new();
    for r in rows {
        if r.len() != 13 {
            return Err("crop parameter row needs 13 columns".into());
        }
        let n: Result<Vec<f64>, _> = r[1..].iter().map(|x| x.parse::<f64>()).collect();
        let v = n.map_err(|_| "invalid numeric crop parameter")?;
        let cp = CropParam {
            base: v[0],
            optimum: v[1],
            ceiling: v[2],
            maturity: v[3],
            rue: v[4],
            max_lai: v[5],
            root_mm: v[6],
            hi: v[7],
            n_frac: v[8],
            fixation: v[9],
            grain_n: v[10],
            n_dilution: v[11],
        };
        if !cp.valid() {
            return Err(format!("invalid parameters for {}", r[0]));
        }
        if map.insert(r[0].clone(), cp).is_some() {
            return Err("duplicate crop".into());
        }
    }
    let get = |s: &str| {
        map.get(s)
            .copied()
            .ok_or_else(|| format!("missing crop {s}"))
    };
    Ok([
        get("corn")?,
        get("soy")?,
        get("oat")?,
        get("rye")?,
        get("clover")?,
    ])
}

#[cfg(test)]
mod tests {
    use super::*;
    fn soil() -> Soil {
        Soil {
            id: "test".into(),
            capacity: [30., 60., 110.],
        }
    }
    fn p() -> [CropParam; 5] {
        [CropParam {
            base: 0.,
            optimum: 25.,
            ceiling: 40.,
            maturity: 1400.,
            rue: 2.5,
            max_lai: 5.,
            root_mm: 900.,
            hi: 0.4,
            n_frac: 0.025,
            fixation: 0.,
            grain_n: 0.02,
            n_dilution: 0.4,
        }; 5]
    }
    #[test]
    fn storm_water_closes() {
        let s = soil();
        let mut st = State::new(&s, 1.);
        let before = st.water_total();
        let mut f = Flux::default();
        infiltrate(&mut st, &s, 150., 0., &mut f);
        assert!((before + 150. - st.water_total() - f.runoff - f.drainage).abs() < 1e-10);
        assert!(f.runoff > 0. && f.drainage > 0.);
    }
    #[test]
    fn dry_soil_cannot_supply_water() {
        let mut w = [0.; 3];
        assert_eq!(
            allocate_water(&mut w, &[4., 3.], &[900., 500.]),
            vec![0., 0.]
        );
    }
    #[test]
    fn competition_is_order_invariant() {
        let mut a = [10., 20., 30.];
        let mut b = a;
        let x = allocate_water(&mut a, &[4., 8.], &[500., 1000.]);
        let y = allocate_water(&mut b, &[8., 4.], &[1000., 500.]);
        assert!((x[0] - y[1]).abs() < 1e-10);
        assert_eq!(a, b);
    }
    #[test]
    fn decomposing_high_cn_residue_never_creates_n() {
        let mut st = State::new(&soil(), 0.5);
        st.mineral_n = 0.;
        st.residue = Organic { c: 10000., n: 1. };
        let before = st.nitrogen_total();
        let mut f = Flux::default();
        decompose(&mut st, 25., 0.8, 1., &mut f);
        assert!(st.mineral_n >= 0.);
        assert!((st.nitrogen_total() - before).abs() < 1e-9);
    }
    #[test]
    fn full_day_water_c_n_close() {
        let s = soil();
        let mut st = State::new(&s, 0.5);
        st.sow(Species::Corn);
        st.plants[0].dm = 500.;
        st.plants[0].n = 12.5;
        let d = step(
            &mut st,
            &s,
            Weather {
                year: 2013,
                doy: 180,
                tmin: 15.,
                tmax: 30.,
                rain: 90.,
                rad: 25.,
            },
            &p(),
            1.,
            1.,
            100.,
        );
        assert!(d.water_error.abs() < 1e-9);
        assert!(d.carbon_error.abs() < 1e-8);
        assert!(d.nitrogen_error.abs() < 1e-8);
    }
    #[test]
    fn legume_fixation_balances() {
        let s = soil();
        let mut st = State::new(&s, 0.8);
        st.sow(Species::Soy);
        st.plants[0].dm = 1000.;
        st.plants[0].n = 25.;
        let mut cp = p();
        cp[1].fixation = 0.7;
        let d = step(
            &mut st,
            &s,
            Weather {
                year: 2013,
                doy: 180,
                tmin: 16.,
                tmax: 29.,
                rain: 0.,
                rad: 24.,
            },
            &cp,
            1.,
            1.,
            0.,
        );
        assert!(d.flux.fixation > 0.);
        assert!(d.nitrogen_error.abs() < 1e-8);
    }
    #[test]
    fn harvest_exports_only_recorded_mass() {
        let mut st = State::new(&soil(), 0.5);
        st.sow(Species::Corn);
        st.plants[0].dm = 10000.;
        st.plants[0].n = 200.;
        st.plants[0].gdd = 1400.;
        let c = st.carbon_total();
        let n = st.nitrogen_total();
        let mut f = Flux::default();
        let y = st.end_crop(Species::Corn, p()[0], &mut f);
        assert!((y - 3200.).abs() < 1e-9);
        assert!((st.carbon_total() + f.harvested_c - c).abs() < 1e-9);
        assert!((st.nitrogen_total() + f.harvested_n - n).abs() < 1e-9);
    }
    #[test]
    fn immature_crop_does_not_export_full_grain() {
        let mut st = State::new(&soil(), 0.5);
        st.sow(Species::Corn);
        st.plants[0].dm = 10000.;
        st.plants[0].n = 200.;
        st.plants[0].gdd = 400.;
        let mut f = Flux::default();
        assert_eq!(st.end_crop(Species::Corn, p()[0], &mut f), 0.);
    }
    #[test]
    fn killing_cover_keeps_all_n() {
        let mut st = State::new(&soil(), 0.5);
        st.sow(Species::Rye);
        st.plants[0].dm = 3000.;
        st.plants[0].n = 60.;
        let n = st.nitrogen_total();
        let mut f = Flux::default();
        assert_eq!(st.end_crop(Species::Rye, p()[3], &mut f), 0.);
        assert!((st.nitrogen_total() - n).abs() < 1e-9);
    }
    #[test]
    fn invalid_weather_rejected() {
        assert!(!Weather {
            year: 2013,
            doy: 1,
            tmin: 20.,
            tmax: 10.,
            rain: 0.,
            rad: 5.
        }
        .valid());
    }
    #[test]
    fn cover_reduces_runoff() {
        assert!(runoff(100., 1.) < runoff(100., 0.));
    }
    #[test]
    fn nitrogen_dilution_preserves_increasing_total_demand() {
        let cp = p()[0];
        assert!(cp.critical_n(2000.) > cp.critical_n(1000.));
        assert!(cp.critical_n(2000.) / 2000. < cp.critical_n(1000.) / 1000.);
    }
    #[test]
    fn ammonium_is_not_immediately_all_leached() {
        let s = soil();
        let mut st = State::new(&s, 1.);
        st.mineral_n = 0.;
        st.ammonium_n = 100.;
        st.som.n = 0.;
        st.residue.n = 0.;
        let d = step(
            &mut st,
            &s,
            Weather {
                year: 2013,
                doy: 10,
                tmin: -2.,
                tmax: 2.,
                rain: 400.,
                rad: 0.,
            },
            &p(),
            1.,
            1.,
            0.,
        );
        assert!(d.flux.leach < 2.);
        assert!(st.ammonium_n > 98.);
        assert!(d.nitrogen_error.abs() < 1e-9);
    }
    #[test]
    fn zero_nitrogen_limits_nonlegume_growth() {
        let s = soil();
        let mut st = State::new(&s, 0.8);
        st.mineral_n = 0.;
        st.ammonium_n = 0.;
        st.som.n = 0.;
        st.residue.n = 0.;
        st.sow(Species::Corn);
        step(
            &mut st,
            &s,
            Weather {
                year: 2013,
                doy: 180,
                tmin: 15.,
                tmax: 30.,
                rain: 0.,
                rad: 25.,
            },
            &p(),
            1.,
            1.,
            0.,
        );
        assert_eq!(st.plants[0].dm, 0.);
    }
    #[test]
    fn buried_roots_are_not_surface_cover() {
        let s = soil();
        let mut a = State::new(&s, 0.8);
        a.sow(Species::Corn);
        a.plants[0].dm = 10000.;
        a.plants[0].n = 200.;
        a.plants[0].gdd = 1400.;
        let mut b = a.clone();
        b.partition_roots = false;
        let mut f = Flux::default();
        a.end_crop(Species::Corn, p()[0], &mut f);
        b.end_crop(Species::Corn, p()[0], &mut Flux::default());
        assert!(a.root_residue.c > 0.);
        assert!(a.cover(&p()).1 < b.cover(&p()).1);
        assert!((a.carbon_total() - b.carbon_total()).abs() < 1e-9);
        assert!((a.nitrogen_total() - b.nitrogen_total()).abs() < 1e-9);
    }
    #[test]
    fn corn_grain_fill_has_duration_not_just_hot_day_accumulation() {
        let mut st = State::new(&soil(), 0.8);
        st.sow(Species::Corn);
        let plant = &mut st.plants[0];
        plant.anthesis_age = Some(60);
        plant.age = 80;
        plant.gdd = 3000.;
        assert!(plant.progress(p()[0], true) < 1.);
        plant.age = 120;
        assert_eq!(plant.progress(p()[0], true), 1.);
    }
    #[test]
    fn photoperiod_slows_soybean_not_maize() {
        assert!(daylength(42.04, 172) > daylength(42.04, 355));
        assert!(
            development_factor(Species::Soy, 16., 14., 0.2)
                < development_factor(Species::Soy, 12., 14., 0.2)
        );
        assert_eq!(development_factor(Species::Corn, 16., 14., 0.2), 1.);
    }
    #[test]
    fn dynamic_fixation_is_suppressed_when_mineral_n_satisfies_demand() {
        let soil = soil();
        let params = p();
        let mut st = State::new(&soil, 0.8);
        st.sow(Species::Soy);
        st.dynamic_fixation = true;
        st.mineral_n = 1000.;
        st.plants[0].dm = 3000.;
        st.plants[0].n = params[1].critical_n(3000.);
        st.plants[0].gdd = params[1].maturity * 0.5;
        let w = Weather {
            year: 2020,
            doy: 190,
            tmin: 18.,
            tmax: 28.,
            rain: 0.,
            rad: 20.,
        };
        let d = step(&mut st, &soil, w, &params, 1., 1., 0.);
        assert_eq!(d.flux.fixation, 0.);
        assert!(
            d.nitrogen_error.abs() < 1e-8
                && d.carbon_error.abs() < 1e-8
                && d.water_error.abs() < 1e-8
        );
    }
    #[test]
    fn reference_et_input_controls_bare_soil_demand_with_closed_water_balance() {
        let soil = soil();
        let mut st = State::new(&soil, 0.8);
        st.residue = Organic { c: 0., n: 0. };
        st.reference_et0 = Some(4.);
        let d = step(
            &mut st,
            &soil,
            Weather {
                year: 2020,
                doy: 190,
                tmin: 18.,
                tmax: 28.,
                rain: 0.,
                rad: 20.,
            },
            &p(),
            1.,
            1.,
            0.,
        );
        assert!((d.flux.evap - 4.).abs() < 1e-9);
        assert!(d.water_error.abs() < 1e-9);
    }
}

#[cfg(test)]
mod eo_tests {
    use super::*;
    #[test]
    fn mulch_reduces_but_does_not_eliminate_potential_soil_evaporation() {
        assert_eq!(organic_mulch_attenuation(0.), 1.);
        assert_eq!(organic_mulch_attenuation(0.5), 0.75);
        assert_eq!(organic_mulch_attenuation(1.), 0.5);
    }
    #[test]
    fn fixation_capacity_is_bounded_by_phenology_water_and_demand() {
        assert_eq!(fixation_capacity(10., 0.8, 0., 1.), 0.);
        assert_eq!(fixation_capacity(10., 0.8, 0.5, 0.), 0.);
        assert_eq!(fixation_capacity(10., 0.8, 1.1, 1.), 0.);
        assert_eq!(fixation_capacity(10., 0.8, 0.5, 1.), 8.);
    }
}
