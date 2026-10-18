# 32 项市场结构候选合同

NO LIVE MONEY。14 项仅合成实现，18 项仅合同；真实来源均为 REAL_RESEARCH_BLOCKED。

每个合同的输入、单位、历史边界和缺失策略另存于机器目录 catalog.json；不因多频率重复计数。

|合同|类别|原生粒度|状态|定义|
|---|---|---|---|---|
|IND_RET|industry|industry|合成实现|G(return)|
|IND_REL_RET|industry|security|合成实现|return-weighted_mean(affiliated industry returns; includes self)|
|IND_AMOUNT_SHARE|industry|industry|合成实现|sum(weight*amount)/market_amount|
|IND_RET_DISPERSION|industry|industry|仅合同|sqrt(G((return-G(return))**2))|
|IND_MEMBERSHIP_CHURN|industry|industry|仅合同|1-Jaccard(current,previous-window members)|
|THEME_ADVANCE_RATIO|concept|concept|合成实现|G(return>0)|
|THEME_MEMBERSHIP_COUNT|concept|security|合成实现|count(distinct active themes)|
|THEME_RET|concept|concept|仅合同|G(return)|
|THEME_OVERLAP|concept|security|仅合同|mean(pairwise Jaccard of affiliated theme member sets); k<2 missing|
|THEME_MEMBERSHIP_CHURN|concept|concept|仅合同|1-Jaccard(current,previous-window members)|
|SC_UPSTREAM_COUNT|supply_chain|security|合成实现|count(distinct confirmed suppliers)|
|SC_DOWNSTREAM_COUNT|supply_chain|security|合成实现|count(distinct confirmed customers)|
|SC_UPSTREAM_RET|supply_chain|security|合成实现|equal_mean(distinct confirmed suppliers' window returns)|
|SC_DOWNSTREAM_RET|supply_chain|security|仅合同|equal_mean(distinct confirmed customers' window returns)|
|SC_NEIGHBOR_RET_DISPERSION|supply_chain|security|仅合同|population_std(distinct suppliers/customers' returns)|
|SC_RELATION_CHURN|supply_chain|security|仅合同|1-Jaccard(current,previous-window directed neighbor sets)|
|BREADTH_ADVANCE_RATIO|breadth|market|合成实现|count(return>0)/count(valid return)|
|BREADTH_LIMIT_UP_RATIO|breadth|market|合成实现|count(window-end limit_state=UP)/count(known limit_state)|
|BREADTH_LIMIT_DOWN_RATIO|breadth|market|合成实现|count(window-end limit_state=DOWN)/count(known limit_state)|
|BREADTH_ABOVE_MA20|breadth|market|仅合同|share(close>mean(previous 20 completed session closes))|
|BREADTH_NEW_HIGH20|breadth|market|仅合同|share(close>max(previous 20 completed session closes))|
|FLOW_NET_ACTIVE_RATIO|flow|security|合成实现|(aggressor_buy-aggressor_sell)/amount only if unclassified=0|
|FLOW_INDUSTRY_NET_RATIO|flow|industry|仅合同|sum(weight*(buy-sell))/industry_amount|
|FLOW_MARKET_NET_RATIO|flow|market|仅合同|sum(buy-sell)/market_amount|
|FLOW_SIGN_PERSISTENCE5|flow|security|仅合同|mean(sign(net active amount),last 5 consecutive completed windows)|
|FLOW_DEFINED_LARGE_ORDER_RATIO|flow|security|仅合同|net active amount of single trades>=1000000 CNY/total amount|
|SENTIMENT_AMOUNT_HHI|sentiment|market|合成实现|sum((amount/market_amount)**2)|
|SENTIMENT_INDUSTRY_DIFFUSION|sentiment|market|合成实现|count(valid industry return>0)/count(valid industry)|
|SENTIMENT_TOP5_AMOUNT_SHARE|sentiment|market|仅合同|sum(largest min(5,N) security amounts)/market_amount|
|SENTIMENT_THEME_DIFFUSION|sentiment|market|仅合同|count(valid theme return>0)/count(valid theme)|
|SENTIMENT_RETURN_SIGN_ENTROPY|sentiment|market|仅合同|-sum(p*log(p),positive/flat/negative,0log0=0)/log(3)|
|SENTIMENT_ADVANCING_AMOUNT_SHARE|sentiment|market|仅合同|sum(amount where return>0)/sum(amount with valid return)|
