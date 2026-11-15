"""Create release gates and a traceable report; never promote diagnostic outputs to advice."""
from pathlib import Path
import json,shutil
import pandas as pd
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];P=R/'processed';O=REPO/'outputs/field-admission-v2';O.mkdir(parents=True,exist_ok=True)
def load(name):return json.loads((P/name).read_text())
def main():
 h=load('hydraulic_audit_summary.json');m=load('management_audit_summary.json');v=load('field_replay_evaluation.json');e=load('economic_audit_summary.json')
 gates=[
 {'id':'H1','item':'Measured BD, texture, SOC/N at 0–100 cm','status':'partial','support':'40 layers, eight 2014 plots, rotations 2 and 4; exact core date and deep rotation 3 absent'},
 {'id':'H2','item':'Retention, conductivity, initial water and water-table/drainage boundary','status':'open','support':'80 declared PTF layer candidates, not measured LL/DUL/Ksat; initial-state date unverified'},
 {'id':'M1','item':'Traceable original operations and principal N basis','status':'partial','support':'1168 source clusters, 1123 dated, 40 date conflicts; verified 2013 C4 and 2014 main N; duplicates and scope need adjudication'},
 {'id':'M2','item':'Complete unique field-year event ledger','status':'open','support':'2014 organic-amendment N assay blank, incidental UAN and subplot scope unresolved; exact zero irrigation not independently confirmed'},
 {'id':'E1','item':'Published historic financial comparison','status':'admitted_with_limits','support':'2008–2012 crop-phase estimated returns; GE and Non-GE stratification; equal-phase annualization'},
 {'id':'E2','item':'Field-year full CBA and current offtake','status':'open','support':'Seed prices alone do not close machinery, labor, manure, transport, drying, land and all receipts; no verified oat/alfalfa buyer contract'},
 {'id':'V1','item':'Source-driven process-model replay','status':'diagnostic_only','support':'32 Rust runs, four corn plots, one weather year; persistent yield and water bias; no newly fitted parameters'},
 {'id':'V2','item':'Independent rotation effect validation','status':'open','support':'No complete oat/clover/alfalfa/rye sequence process validation or independent multi-year field holdout'},
 {'id':'F1','item':'Farmer weights and actual usability testing','status':'open','support':'Testing kit ready; zero real farmer participants'},
 ]
 bundle={'version':'field-records-v2','date':'2026-11-15','site':'Marsden Farm, Boone County, Iowa','measured_soil_layers':h['measured_layers'],'measured_profiles':8,'source_event_clusters':m['source_event_clusters'],'date_conflicts':m['date_conflicts'],'replay':v,'financial_cases':pd.read_csv(P/'historical_financial_point_order.csv').to_dict('records'),'gates':gates,'operational_recommendation_eligible':False,'full_CBA_eligible':False,'full_MCA_eligible':False,'real_farmer_participants':0,'sources':{'author_repository':'https://github.com/vanichols/maRsden/tree/01476a18c01115f70f154cf7e94c1951205fbda1','soil_paper':'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0164209','economics_paper':'https://ageconsearch.umn.edu/record/205805/files/AAEA%202015%20paper.pdf','PTF':'https://doi.org/10.2136/sssaj2005.0117'},'financial_scope':'Historical published estimated returns, USD/ac/year, 2008–2012. No current prices, statistical superiority or operational recommendation. GE/Non-GE management packages are not isolated genetic effects.'}
 (P/'admission_gates.json').write_text(json.dumps(bundle,indent=2,ensure_ascii=False)+'\n')
 shutil.copy(P/'admission_gates.json',O/'admission_gates.json')
 report='''# 田块记录补齐、模型回放与经济比较｜第二阶段核验

日期：2026-11-15。研究区：美国 Iowa 州 Boone County 的 Marsden 长期试验。主结论：已补入真实分层土壤和原始管理日志，完成实际 Rust 回放；完整水力边界、逐项经济账与轮作效应验证仍未闭合，因此本阶段没有发布实用轮作推荐排名。

## 1. 准入清单更新

|项目|本次实际取得／完成|状态与适用范围|
|---|---|---|
|分层土壤|2014 年 40 层、8 小区，0–100 cm 的容重、质地、SOC、总 N、采样质量和体积|两年与四年轮作；三年系统深层仍缺。必须纠正此前“容重缺失”的概括。不是新增采样，原始公开数据此前未充分审计|
|浅层过程观测|2016 年论文 S1 数据 360 行，281 行具有容重／WFPS 配对|覆盖两／三／四年系统，0–20 cm，2008 秋至 2010 春五个采样期；季节标签不能伪造成逐日日期|
|水力参数|由质地和有机质假设估计 80 个土层候选，形成 16 个物理可行剖面候选|LL15／DUL33 是 PTF 先验，SAT 是容重孔隙率代理；没有取得实测持水曲线或 Ksat|
|管理日志|固定作者仓库版本，下载并校验 21 个文件；整理 1,168 个原始事件片段，1,123 个可解析日期，40 个日期／表名年份冲突|跨来源有重复，含续行和自由文本；不是 1,168 个唯一完整管理事件。冲突保留，不自动更正|
|施氮核查|修正 2013 C4 范围重叠；2014 C2 两次主要矿质 N 合计 168.13 kg N/ha|小区附带 UAN、2014 有机肥 N 化验与残留状态尚未闭合；“主要施氮”不等于“全部 N”|
|经济证据|原始日志玉米／大豆种价；2015 AAEA 论文表 1 的 15 个历史作物阶段收益估算|可做注明年份、技术包和口径的历史比较；不能替代同田块年完整费用账及当前买家合同|
|模型运行|实际编译并完成 32 次 Rust 回放，输入、源码、二进制散列和运行日志留档|仅 2014 两年轮作玉米 4 小区、一个天气年；没有运行官方 APSIM，也未声称等价重实现|
|农户测试|沿用已有同意、任务、记录和分析工具|真实参与者仍为 0，没有生成模拟农户意见|

## 2. 水力参数与土壤水分单位

实测土层为 0–15、15–30、30–60、60–90、90–100 cm。容重由原始干重／有效体积复核，差异小于 0.01 g/cm³；实测容重范围约 1.09–1.85 g/cm³。按 SOC/OM=0.58 和 0.50 两个假设转换有机质，利用 Saxton–Rawls 质地／有机质经验式生成持水先验。假定颗粒密度 2.65 g/cm³ 计算孔隙率，未将其叫作实测饱和含水量，也未通过裁剪把不合格值变成合格值。先验检查满足 0<LL<DUL<孔隙率，不代表当地水力学已经验证。

相同 2014 小区有 256 个分层水分记录，可在条件假设下使用 θv=θg×ρb/ρwater 转为体积含水量。0–10 cm 映射到 0–15 cm 容重；10–30 cm 按 5 cm 与 15 cm 厚度加权。此转换依赖 g/g 为干土质量基准、容重层内均一，以及采样时间差异不影响代表性的假设。它不是直接 VWC 实测。2013 水分没有偷偷配上 2014 容重，含义不清的 0–30 cm 汇总值未准入。

2018 传感器安装表中的 dry_VWC／sat_VWC 不能直接视为土层 LL／SAT。部分干点读数为负，须先取得设备、标定与现场安装协议。浅层 WFPS 是充水孔隙比例；储水状态也不能直接变成蒸散、需水或节水量。

## 3. 已核实的管理输入与仍缺部分

- 原始 Dates-all 第 764 行，2013-06-28：C2 100、C3 75、C4 **50 lb N/ac**。C4 不是 75+50。后续参数化不得沿用该重复归属。
- Woods 2014 表第 4、25 行：2014-04-21 C2 100 lb N/ac；2014-06-11 C2 50，C3/C4 各 25 lb N/ac。原文已是养分 N 基准，不能再乘 32% UAN 浓度。
- 2014 玉米：4 月 22 日播种，Viking 72O4N、104-day、32,200 seeds/ac；10 月 6 日收获。回放使用真实日期，但当前简化模型未显式表达该杂交种、株密度、P/K 和耕作效应。
- 2012 秋施、归入 2013 玉米的堆肥记录有 55.8% 干物质、1.08% N 与约 85 lb 总 N/ac；总 N 不等于当季有效 N。2013 秋、归入 2014 的记录有 72.5% 干物质，但 N/P/K 化验空白，不能借用上一批次补值。
- 2014 种子原始报价：玉米 $152/80,000 seeds，按记录密度算 $61.18/ac；源表近似写 $61.50/ac，保留 $0.32 差异。大豆 $57/140,000 seeds，按 160,000 seeds/ac 为 $65.14/ac。不能据此声称完整成本已补齐。
- Woods 工作簿名为“2013”的工作表有 38 个记录日期在 2019 年；另有原始日记两处年份冲突。保留原值与出处，等待作者解释，不作为已核实 2013 日历。

完整事件账仍需逐条去重、确认处理／子区范围和“缺失／未实施／零投入”的差别。未发现灌溉事件不是独立证明灌溉为零。不得把假定耕作表升级为实测记录。

## 4. 实际模拟及评估结果

预先锁定的诊断设计：4 小区×2 种 SOC/OM 假设×4 个初始有效水比例（0.2、0.4、0.6、0.8）=32 次。沿用冻结的 v0.2 作物参数，不针对这 4 个产量重新拟合、不只挑最好组合。采用既有 NASA POWER 区域逐日强迫；真实 2014 SOC／全氮库存被用作年初有机库代理，但实际采样日期未知；全氮未分离矿质氮，另设初始矿质 N 会有口径重叠风险。初始矿质 N=50 kg/ha、表层残体 C=1,000/N=15 kg/ha、organic_mulch=true 仍是模型设定，并非实测管理。三层有效水桶不是完整 Richards 流、水位或暗管排水模型。

|检验量|实际结果|解释|
|---|---|---|
|玉米均产，统一至 15.5% 含水率|观测 203.78；模拟 188.78–194.28 bu/ac|平均低估 9.50–15.00 bu/ac|
|玉米小区 RMSE|11.08–16.62 bu/ac|4 小区、1 年，不是跨地区／多年验收|
|0–30 cm 条件储水 RMSE|19.18–19.65 mm|64 个小区日期，不是 64 个独立天气样本|
|0–30 cm 条件储水偏差|+13.16–14.00 mm|水分总体偏湿|
|同一时段每小区恒定均值参照|RMSE 12.11 mm|使用观测自身计算的样本内描述参照，不是可部署预测模型；回放尚未优于它|
|水／C／N 守恒|32 次均通过|数值守恒必要，但不证明过程和预测准确|

以上区间是全部设定组合的范围，**不是置信区间**。新土壤／日期／N 输入一次同时替换，不能把误差变化单独归因于某一项。没有在相同评估协议下重跑旧输入，故不宣称已量化提升幅度。该轮也未验证大豆、黑麦、燕麦、三叶或苜蓿替代方案的完整过程效应。

优先修正方向：先核对区域降雨与田块天气、蒸散与有效水／排水边界、物候和株密度，再处理 N 可利用性、根系与 C/N 分配。初始水情景下水分 RMSE 变化较小，单调初始水比例不足以说明偏湿问题已经解决。当前没有实测 ET 或灾损因果标签，不把残差直接归因为极端天气、病虫害或灌溉。

## 5. 可以复核的历史经济比较

来源为 Kranti Mulik 的 2015 AAEA/WAEA 会议论文表 1（PDF 第 11 页），2008–2012 年估算，非本次独立取得的现金账，也不标为期刊同行评审结果。按表注，口径为扣除土地、人工费用后的管理回报。它与此前 Davis 2012 的土地与管理回报（排除土地等）口径不同，不能混合排名。

按等面积作物阶段计算年度化均值，区分 GE／Non-GE 技术包（不推断纯遗传效应）：

|历史技术包|两年：玉米—大豆|三年：玉米—大豆—燕麦／红三叶|四年：玉米—大豆—燕麦／苜蓿—苜蓿|历史点估计顺序|
|---|---:|---:|---:|---|
|GE|217.30|208.97|192.00|两年 > 三年 > 四年|
|Non-GE|190.06|217.05|199.77|三年 > 四年 > 两年|

单位：历史 USD/ac/年。每阶段权重为 1/轮作年数；是同一时点不同阶段的等面积组合，不是已贴现的转型现金流。没有系统级标准误、完整年度协方差，不能声称显著优胜。GE 两年与 Non-GE 三年的均值仅差约 $0.25/ac/年，不能据此挑选赢家。这里的四年系统不含黑麦，不能替代应用中的黑麦方案证据。

另计算每种技术包 81 个共同价格加减情景：玉米 ±$2/bu、大豆 ±$4/bu、燕麦 ±$1/bu、苜蓿 ±$40/ton（各含零变动）。这是对每个历史年价格的共同加法扰动，固定产量、费用、销路，不是当前价格预测。GE 三系统分别在 43／15／23 个设定中列财务点估计第一；Non-GE 为 26／29／26。网格无概率权重，不能解释成获胜概率。气候、政策或地缘政治冲击可转化为明确情景，但不能编造其发生概率、产量响应或市场合同。

不能用“平均产量×平均价格−平均收益”反推真实平均成本，因为缺少年际价格—产量协方差和原始核算细目。论文表 2 的四年 N 年均值还存在算术口径疑点，未拿来作验证后的 MCA 指标。

## 6. 下一道可执行门槛

1. **水力／边界闭合**：索取同小区深层三年系统数据、带日期初始含水／硝态氮／铵态氮、持水曲线与 Ksat、暗管与地下水边界、田块降雨／温度及传感器标定。将估计先验和实测分开保留。
2. **事件账闭合**：确认 2013 年表名冲突、2013 秋堆肥原始化验、全部施用范围、附带 UAN、实际灌溉或明确零记录；记录播种、终止、耕作、保护、收获与残体去向。草拟索取清单已交付，本轮未联系作者或农户。
3. **模型验收后再拟合轮作效应**：先用实测物候／水分联合约束少量可识别参数；以年份／管理系统留出，避免随机拆分重复小区日期。先解决偏湿，再检查根系、N 供需与 C/N 分配。不得只调 RUE 抵消未知水／N 输入。训练期校准，锁定期同时报告绝对值与处理差值、朴素基线和区间覆盖。
4. **CBA／MCA**：取得同田块年逐项收入和费用、黑麦完整增量费用、燕麦／苜蓿真实到场收购条件后，计算完整轮作周期增量净现值／年金、转换与终期存量，进行价格、成本与气候情景敏感性分析。MCA 先做水、机具、农艺和销路可行性筛选，再由农户给权重和价值锚点，避免收益、净现值重复计分。缺项不填零、不自动重新分配权重，输出部分可比较性与无法判定。
5. **现场验证与使用测试**：沿用已有农户任务包，实际招募后记录理解、误用和可完成性，再开展成对条带／随机区组对照；在完整轮作周期验证替代方案，而非用同一年的四小区校准结果当推荐验收。

## 7. 文件、复现与来源

- `case-study/field-admission-v2/`：固定来源与散列、原始日志／土壤／论文、规范化表、协议、模型输入输出和 Rust／Python 源码。
- `processed/admission_gates.json`：机器可读准入状态；完整 CBA、MCA、实用推荐资格均为 false。
- `src/verify_admission.py`：10 项来源完整性、单位、关联、施肥范围、模拟组合、守恒和发布边界检查，全部通过；不等价于农户或独立田块验证。
- 复现说明与最小依赖随独立 ZIP 交付；旧版研究包和冻结参数保留。

来源：

- 作者仓库：<https://github.com/vanichols/maRsden/tree/01476a18c01115f70f154cf7e94c1951205fbda1>。固定提交与 Git blob/SHA-256 双重校验；保留 MIT 许可。
- Lazicki, Liebman & Wander (2016)：<https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0164209>，S1/S2，CC BY。
- Mulik (2015)：<https://ageconsearch.umn.edu/record/205805/files/AAEA%202015%20paper.pdf>，表 1 原页已渲染目视核对。保留原版权页，只作非商业研究复核。
- Saxton & Rawls (2006)：<https://doi.org/10.2136/sssaj2005.0117>；质地／有机质函数仅作参数先验。镜像全文下载 404 已记录为失败，未计作成功获取。
'''
 (O/'Field_Admission_Validation_Report_CN.md').write_text(report)
 (O/'Researcher_Record_Request_Draft.md').write_text('''# 数据交接请求草稿（未发送）

研究对象：Marsden，小区 13/24/34/44（两年玉米）与 18/28/37/46（四年玉米），并扩展三年系统。请优先提供原始记录及单位、样本／管理空间范围，不必重制汇总图。

1. 2014 分层容重／SOC/N 原始采样日期、石砾／细土质量与体积基准；三年系统 20–100 cm 数据；同小区持水曲线、Ksat、暗管／水位和初始带日期分层水分、NO3-N／NH4-N。
2. 2013 秋堆肥批次原始化验：N/P/K、干湿质量、密度与施用位置；2014 附带喷施 UAN 的产品浓度、密度、体积、有效面积／子区；确认全部播种、耕作、除草、保护、终止、收获与残体事件，灌溉若为零请给明确记录。
3. Woods 2013–2018 工作簿中“2013”页实际日期均为 2019 的解释；Dates-all 第 719/779 行年份冲突的确认；来源间重复事件的优先级。
4. 同小区年逐项投入、实价与费用分摊：种子、N/P/K、堆肥材料／装运／撒施、药剂与作业、劳动、机具折旧／资本、燃油、干燥／仓储／运输、土地、保险／融资；全部实收收入、补助、燕麦草及苜蓿多茬／库存。请说明是否现金／经济成本、有无重复计价。
5. 燕麦／苜蓿可核实收购条款、用途、质量／水分标准、最低数量、交付点、运距、扣价、保险与付款期。历史试验估算不替代当前采购合同。
6. 匹配田块天气、实测物候、株密度／杂交种、田间病虫／倒伏／冰雹／淹水灾损，以及传感器型号、原始输出、标定与采样深度。

本草稿未发出；本轮未以用户身份联系研究者、买家或农户。缺失保留为空，不能以相近年份、县均值或零值替换为实测。
''')
 print(json.dumps({'report':str(O/'Field_Admission_Validation_Report_CN.md'),'gates':len(gates),'operational_recommendation_eligible':False},ensure_ascii=False))
if __name__=='__main__':main()
