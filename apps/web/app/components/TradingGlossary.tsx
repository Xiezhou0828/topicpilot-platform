const TERMS = [
  ["進場條件分數", "進場條件的完整程度", "分數高仍需等觸發", "條件或價格失效時停止觀察"],
  ["觀察資格", "後端是否允許列入觀察", "PASS 只代表可觀察", "缺觸發價或資料過期時不採用"],
  ["回檔轉強", "拉回後重新出現買盤", "等站回關鍵價", "跌破失效價即停止觀察"],
  ["等突破", "價格仍在觸發價下方", "等待有效突破", "不提前追價"],
  ["波段新高等回測", "突破後等待回測確認", "觀察支撐是否守住", "跌回失效價下方即結束"],
  ["雙週期領先", "短中期相對強度皆領先", "優先追蹤但仍等價格確認", "相對強度轉弱時降級"],
  ["資金先行", "資金訊號早於消息反映", "確認價格與量能", "資金退潮時不追"],
  ["消息共振", "題材、消息與價格同向", "確認不是單日反應", "消息與價格背離時停止追蹤"],
  ["族群分歧", "同題材個股漲跌不一致", "只留強勢標的", "廣度持續收斂時降低優先"],
  ["細分主導", "漲勢集中在特定子題材", "聚焦真正領漲分支", "主導分支轉弱時重新評估"],
] as const;

export function TradingGlossary() {
  return (
    <details className="panel glossaryPanel">
      <summary>交易術語白話說明</summary>
      <div className="glossaryGrid">
        {TERMS.map(([term, meaning, action, invalid]) => (
          <article key={term}>
            <strong>{term}</strong>
            <span><b>意思</b>{meaning}</span>
            <span><b>動作</b>{action}</span>
            <span><b>失效</b>{invalid}</span>
          </article>
        ))}
      </div>
    </details>
  );
}
