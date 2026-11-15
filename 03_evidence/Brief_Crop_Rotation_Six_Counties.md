# Crop rotations in six US counties: cash crops, grains, forage

**Counties:** Brown, Riley, Saline (KS); Canyon, Gem, Twin Falls (ID). Cut-off 15 Nov 2026.

## Bottom line

The six counties do not share one rotation logic.

- **Kansas is grain-to-grain.** Brown is a tight two-year corn–soybean alternation: 88.3% of corn sample centres followed soybean, only 9.1% followed corn (2018–2023); corn plus soybean harvested acreage was 91.5% of county cropland in 2022. Saline is wheat-based (40.6% wheat, 26.6% soybean, 11.4% sorghum of sampled crop-years) with double cropping.
- **Idaho mixes specialty cash crops with forage and small grains.** Twin Falls mixes alfalfa (33%), corn (24%), barley (11%), wheat (9%), dry bean (8%), potato (5%) and sugar beet (4%) of sampled crop-years. Potato returned to the same centre after a median four years (66% of gaps ≥4); sugar beet after three; alfalfa stands ran a median four years.
- **But Idaho corn is often continuous and largely forage.** Corn after corn was 39.5% in Twin Falls, 49.2% in Canyon, 64.0% in Gem. Canyon's corn is about half silage; Twin Falls' is mostly silage. In Canyon and Twin Falls the dairy silage block behaves like a forage monocrop.

So "cash-to-cash versus grain-to-grain" is the wrong axis: in Kansas both rotation partners are sold grains/oilseeds; in Idaho the rotation is specialty–forage–grain, with corn frequently a forage crop.

## 1. Classification used

A US **cash crop** is any crop grown for sale, including corn and wheat ([FAO](https://www.fao.org/4/y5096e/y5096e0v.htm)), not the opposite of "grain". The 粮食/经济 binary is unstable: soybean is an oilseed (油料/经济作物) in crop-economy terms but counted under 粮食 (豆类) in grain-output statistics, and potato is both a 粮食 and a vegetable/industrial crop.

I therefore classify by function and end use, then test whether fields alternate groups: **G** grains/oilseeds (corn, wheat, sorghum, barley, soybean); **S** specialty industrial/vegetable crops (sugar beet, potato, dry bean, onion); **F** forage (alfalfa, other hay, corn silage). Under the user's Chinese convention (soybean as oilseed/经济作物) Brown's corn–soybean is 粮食↔经济; under China's grain-output statistics both are 粮食; under US usage cash↔cash; under my functional test G↔G with a legume break. CDL class 1 cannot separate grain from silage corn; Census can, and that distinction drives the Idaho reading.

## 2. County crop mix (Census of Agriculture, 2022)

Harvested acres ([county profiles](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Kansas/cp20013.pdf); field crops [Kansas](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Kansas/st20_2_025_025.pdf), [Idaho](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_025_025.pdf); hay/silage [Table 26](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_026_026.pdf); potatoes/vegetables [Table 29](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_029_029.pdf)):

| County | Cropland (ac) | Main harvested acres, 2022 |
|---|---:|---|
| Brown, KS | 272,572 | corn 127,026; soybean 122,420; hay 11,401; wheat 2,061; alfalfa 1,927 |
| Riley, KS | 90,613 | soybean 35,764; corn 17,264; hay 10,618; sorghum 3,911; wheat 3,403; alfalfa 2,668 |
| Saline, KS | 203,613 | wheat 83,309; soybean 54,173; sorghum 22,958; hay 22,615; alfalfa 10,303; corn 7,971 |
| Canyon, ID | 228,177 (207,577 irrig.) | wheat 38,781; alfalfa 33,637; corn grain 23,758; corn silage 23,669; sugar beet 13,175; onion 9,922; potato 3,566; dry bean 2,991 |
| Gem, ID | 27,426 (25,735 irrig.) | alfalfa 7,720; hay 10,762; corn 3,254; wheat 2,866; barley 602; potato 9 |
| Twin Falls, ID | 249,600 (236,196 irrig.) | alfalfa 59,958; corn silage 41,145; barley 35,228; wheat 19,625; corn grain 15,650; sugar beet 8,343; dry bean 6,599; potato 5,799 |

County totals, not rotations: presence at scale, not field alternation. Brown has almost no wheat or alfalfa to rotate with; Twin Falls has no crop above one third of cropland.

## 3. Field sequences (CDL 2008–2023, 300 m sample)

Method: the project's fixed 300 m EPSG:5070 grid sampled from official 30 m CDL (8 counties × 17 years), county-masked, restricted to centres cropland in ≥10 of 16 years; 2024 excluded. Transitions come from overlaying consecutive annual CDL rasters and cross-tabulating classes at fixed points; shares are of sampled centre-years 2017–2023 and predecessor shares pool 2018–2023. These are sample centres, not fields, farms or acres; neighbours are correlated.

| County | Centres | Crop-year mix 2017–23 | Corn after corn / soy | Median return gap | Alfalfa run |
|---|---:|---|---|---|---|
| Brown, KS | 10,802 | corn 49.6, soy 48.2, other 2.2 | 9.1% / 88.3% | – | 1 yr |
| Riley, KS | 3,393 | soy 49.5, corn 27.4, wheat 8.6, sorghum 5.4, alfalfa 4.4 | 11.2% / 77.8% | – | 3 yr |
| Saline, KS | 8,843 | wheat 40.6, soy 26.6, sorghum 11.4, DC wheat/soy 7.3, corn 5.1, alfalfa 4.9 | 8.0% / 36.1% | – | 3 yr |
| Canyon, ID | 8,855 | alfalfa 27.1, corn 22.0, wheat 16.0, beet 5.3, onion 4.9, dry bean 4.1, potato 2.5 | 49.2% / ~0% | potato 5; beet 4 | 3 yr |
| Gem, ID | 1,075 | alfalfa 53.1, corn 22.0, wheat 7.9, barley 2.2 | 64.0% / 0% | potato 4 (n=31); beet 3 | 6 yr |
| Twin Falls, ID | 11,476 | alfalfa 33.3, corn 24.3, barley 10.6, wheat 8.6, dry bean 8.4, potato 5.0, beet 4.1 | 39.5% / 0% | potato 4; beet 3 | 4 yr |

*(Percentages; DC = double crop.)*

Two further facts. Potato is rarely consecutive: one-year gaps were 1.7% in Twin Falls and 4.9% in Canyon; ≥4-year gaps were 66.1% and 73.5%. Sugar beet clusters at three to four years (Twin Falls 37.4% three-year, 47.1% ≥4; Canyon 21.7% and 59.6%).

In Saline only 36.1% of corn followed soybean (20.7% double-crop wheat/soy, 18.4% wheat), and soybean followed soybean 31.2% and sorghum 26.0% — a wheat–soy–sorghum system with double cropping; in Riley soybean followed corn only 43.2% (soybean 36.2%). Census 2017→2022 shifts: Brown corn 111,824→127,026 acres; Twin Falls dry beans 20,794→6,599; Canyon dry beans 9,734→2,991.

## 4. Best rigorous source and evidence hierarchy

1. **Field-level, area-weighted: NASS Crop Sequence Boundaries (CSB).** Synthetic field polygons from eight-year CDL stacks, with a majority CDL class per year (e.g., `CDL2018`–`CDL2025` in the 2018–2025 release), polygon acres and county FIPS ([page](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/), [metadata](https://data.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm), [method paper](https://doi.org/10.3233/sji-230078)). For 2017–2023 exactly, use the 2016–2023 layer and ignore 2016 (boundaries still reflect that 8-year stack), or rebuild with the [code](https://github.com/USDA-REE-NASS/crop-sequence-boundaries). Caveats: ~3.5 GB zipped national geodatabase, ~15.97 million polygons, no county subset; I found no published county summary; boundaries are CDL-derived (not FSA Common Land Units), so CDL error (85–95% for major crops) propagates.
2. **Sample-centre sequences (this grid):** best available here for 2008–2023 and return intervals; reproducible, but unweighted and not field-based.
3. **County totals (Census):** authoritative on acreage and end use, silent on sequence.
4. **Guidance/experiments:** K-State's 31-year Manhattan (Riley County) trial found soybean, sorghum and wheat yield more in rotation than continuous no-till; Hesston found corn after wheat or double-crop soybean better than after soybean/sorghum ([MF2908](https://bookstore.ksre.ksu.edu/download/rotations-and-cultural-practices_MF2908)). USDA-ARS evaluated two-, three- and four-year seed-potato rotations with spring wheat, feed barley, oats and canola in southeastern Idaho ([record](https://www.ars.usda.gov/research/publications/publication/?seqNo115=82333)). An Idaho conservation-district plan indexed online says Twin Falls-area rotations "generally last about eight years" and include "alfalfa hay two or three years" ([Snake River SWCD](https://swc.idaho.gov/wp-content/uploads/2023/03/SnakeRiver_FY2024_5YrAnnCert.pdf)). UI Extension PDFs were blocked here.

**No peer-reviewed county-specific estimate** of corn-after-corn, potato frequency or sugar-beet frequency was found for these six counties. The figures above are CDL classifications, not measured farmer practice.

## 5. What the 300 m sample supports

**Supports:** county crop mix; coarse predecessor shares and return-interval distributions; cross-county comparison; a 2008–2023 baseline; identifying specialty–forage versus grain–oilseed systems.

**Does not support:** field/farm claims; acreage weighting (a centre is one 30 m pixel, not a 9 ha average); farmer intent, plans or contracts; small/narrow specialty fields (onion, potato strips); corn grain versus silage; double-crop attribution; causal yield, profit or soil effects; 2024-onward comparability. Return-interval medians are left-truncated by the 16-year window, so long gaps are under-counted and medians biased short. The sample can show rotations differ in kind; it cannot pin prevalence within a few points.

## Sources

- USDA NASS CSB: [program](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/) · [metadata](https://data.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm) · [viewer](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/Viewer/index.php) · [code](https://github.com/USDA-REE-NASS/crop-sequence-boundaries) · [paper](https://doi.org/10.3233/sji-230078)
- USDA NASS CDL: [metadata/classes](https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/meta.php) · [CropScape](https://nassgeodata.gmu.edu/CropScape/) · [CroplandCROS](https://croplandcros.scinet.usda.gov/)
- 2022 Census county profiles: [Brown](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Kansas/cp20013.pdf) · [Riley](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Kansas/cp20161.pdf) · [Saline](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Kansas/cp20169.pdf) · [Canyon](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Idaho/cp16027.pdf) · [Gem](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Idaho/cp16045.pdf) · [Twin Falls](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Online_Resources/County_Profiles/Idaho/cp16083.pdf)
- 2022 Census tables: [KS field crops](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Kansas/st20_2_025_025.pdf) · [ID field crops](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_025_025.pdf) · [ID hay/silage](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_026_026.pdf) · [ID potatoes/vegetables](https://www.nass.usda.gov/sites/default/files/publications/agcensus/2022/Full_Report/Volume_1,_Chapter_2_County_Level/Idaho/st16_2_029_029.pdf)
- K-State MF2908: [PDF](https://bookstore.ksre.ksu.edu/download/rotations-and-cultural-practices_MF2908) · USDA-ARS seed-potato rotations: [record](https://www.ars.usda.gov/research/publications/publication/?seqNo115=82333) · Snake River SWCD: [PDF](https://swc.idaho.gov/wp-content/uploads/2023/03/SnakeRiver_FY2024_5YrAnnCert.pdf)
- FAO cash crop: [link](https://www.fao.org/4/y5096e/y5096e0v.htm)
- Project data: `outputs/crop-rotation-evidence/long_sequence_stats.json`, `county_transitions_2022_2023.csv`, `county_sequences_2021_2023.csv`; CDL TIFFs in `case-study/management-refit/raw/CDL/`.