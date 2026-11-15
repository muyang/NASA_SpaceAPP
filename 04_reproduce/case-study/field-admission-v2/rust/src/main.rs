use fieldshift_eo_rs::*;
use std::{env,fs,path::Path,io::{Write,BufWriter}};
fn rows(path:&Path)->Vec<Vec<String>> {fs::read_to_string(path).expect("input file").lines().skip(1).filter(|s|!s.trim().is_empty()).map(|s|s.split(',').map(str::to_string).collect()).collect()}
fn number(s:&str)->f64 {let x:f64=s.parse().expect("numeric input");assert!(x.is_finite());x}
fn add(t:&mut Flux,f:Flux){t.rain+=f.rain;t.runoff+=f.runoff;t.drainage+=f.drainage;t.evap+=f.evap;t.transp+=f.transp;t.fert+=f.fert;t.fixation+=f.fixation;t.leach+=f.leach;t.growth_c+=f.growth_c;t.harvested_c+=f.harvested_c;t.harvested_n+=f.harvested_n;t.respired_c+=f.respired_c;}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<String>=env::args().collect();if a.len()!=3{return Err("usage: fieldshift-field-replay INPUT OUTPUT; diagnostic only".into());}
 let input=Path::new(&a[1]);let out=Path::new(&a[2]);fs::create_dir_all(out)?;
 let params=params_from_rows(&rows(&input.join("crops.csv")))?;
 let weather=rows(&input.join("weather.csv"));assert_eq!(weather.len(),365);
 let events=rows(&input.join("events.csv"));
 let mut daily=BufWriter::new(fs::File::create(out.join("daily.csv"))?);let mut annual=BufWriter::new(fs::File::create(out.join("annual.csv"))?);
 writeln!(daily,"run,plot,OC_OM,initial_fraction,doy,theta_0_150,theta_150_450,water_0_300_mm,ET_mm,fertilizer_N_kg_ha")?;
 writeln!(annual,"run,plot,OC_OM,initial_fraction,corn_yield_dry_kg_ha,fertilizer_N_kg_ha,water_error_mm,C_error_kg_ha,N_error_kg_ha")?;
 let mut run=0;
 for row in rows(&input.join("soils.csv")) {
  assert_eq!(row.len(),10);let plot=&row[0];let om=number(&row[1]);let soil=Soil{id:plot.clone(),capacity:[number(&row[2]),number(&row[3]),number(&row[4])]};assert!(soil.valid());let ll=[number(&row[5]),number(&row[6]),number(&row[7])];
  for initial in [0.2,0.4,0.6,0.8] {
   run+=1;let mut state=State::new(&soil,initial);state.som=Organic{c:number(&row[8]),n:number(&row[9])};state.reference_et0=Some(0.);state.organic_mulch=true;
   let start=(state.water_total(),state.carbon_total(),state.nitrogen_total());let mut total=Flux::default();let mut grain=0.;
   for (i,w) in weather.iter().enumerate() {
    let day:u32=w[1].parse()?;assert_eq!(day,i as u32+1);let year:i32=w[0].parse()?;assert_eq!(year,2014);
    let weather=Weather{year,doy:day,tmin:number(&w[2]),tmax:number(&w[3]),rain:number(&w[4]),rad:number(&w[5])};assert!(weather.valid());state.reference_et0=Some(number(&w[6]));
    let mut fert=0.;let mut harvest=false;
    for e in &events {if e[0].parse::<u32>()?==day {match e[1].as_str(){"sow"=>state.sow(Species::Corn),"fertilize_N"=>fert+=number(&e[2]),"harvest"=>harvest=true,_=>return Err("unsupported event".into())}}}
    let d=step(&mut state,&soil,weather,&params,1.,1.,fert);add(&mut total,d.flux);
    if harvest {let mut f=Flux::default();grain+=state.end_crop(Species::Corn,params[0],&mut f);add(&mut total,f);}
    let theta=[ll[0]+state.water[0]/150.,ll[1]+state.water[1]/300.];let storage=theta[0]*150.+theta[1]*150.;
    writeln!(daily,"{run},{plot},{om},{initial},{day},{:.9},{:.9},{storage:.8},{:.8},{fert:.8}",theta[0],theta[1],d.flux.evap+d.flux.transp)?;
   }
   let we=start.0+total.rain-total.runoff-total.drainage-total.evap-total.transp-state.water_total();let ce=start.1+total.growth_c-total.harvested_c-total.respired_c-state.carbon_total();let ne=start.2+total.fert+total.fixation-total.leach-total.harvested_n-state.nitrogen_total();
   assert!(we.abs()<1e-6&&ce.abs()<1e-5&&ne.abs()<1e-6,"balance error");
   writeln!(annual,"{run},{plot},{om},{initial},{grain:.8},{:.8},{we:.10},{ce:.10},{ne:.10}",total.fert)?;
  }
 }
 daily.flush()?;annual.flush()?;
 fs::write(out.join("execution_status.json"),format!("{{\"runs\":{run},\"year\":2014,\"scope\":\"diagnostic_only\",\"actual_source_main_N_and_dates\":true,\"hydraulic_retention_is_estimated\":true,\"initial_states_partly_assumed\":true,\"APSIM_executed\":false,\"operational_recommendation_eligible\":false}}\n"))?;
 println!("Completed {run} source-record-driven field diagnostics; conservation passed.");Ok(())
}
