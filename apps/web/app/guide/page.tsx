import Link from "next/link";
import { AppNav } from "../components/AppNav";

const priceTerms = [
  ["觸發價", "後端定義的觀察條件價位；碰到不等於必須採取行動。"],
  ["支撐價", "觀察價格回檔時是否仍守住結構的位置。"],
  ["失效價", "跌破後代表原本觀察假設不再成立。"],
  ["風險幅度", "由既有 snapshot 提供的價格風險距離，用來評估是否超出自己的承受範圍。"],
];

export default function GuidePage() {
  return (
    <main>
      <AppNav />
      <div className="appShell guideShell">
        <header className="topbar guideHeader">
          <div><p className="eyebrow">Product guide</p><h1>使用指南</h1></div>
          <p>題材領航是研究與觀察工具，不是自動下單或獲利保證。</p>
        </header>
        <nav className="guideJump" aria-label="指南章節"><a href="#start">今天先看哪裡</a><a href="#pages">頁面差別</a><a href="#prices">價位怎麼用</a><a href="#safety">何時不能判讀</a><a href="#filters">篩選方式</a></nav>

        <section className="guideSection" id="start">
          <div className="guideSectionTitle"><span>01</span><div><p className="eyebrow">Start here</p><h2>今天先看哪一頁</h2></div></div>
          <ol className="guideSteps">
            <li><strong>今日工作台</strong><span>先看市場狀態、今日動作與下一步，確認資料能不能使用。</span><Link href="/">前往今日</Link></li>
            <li><strong>題材總覽</strong><span>確認資金集中在哪些大族群與細題材，再看廣度與相關股票。</span><Link href="/topics">前往題材</Link></li>
            <li><strong>股票一覽</strong><span>用快速篩選縮小範圍；需要技術細節時再展開進階篩選。</span><Link href="/watchlist">前往股票一覽</Link></li>
            <li><strong>個股明細</strong><span>最後確認觸發、支撐、失效、觀察資格與完整判讀原因。</span></li>
          </ol>
        </section>

        <section className="guideSection" id="pages">
          <div className="guideSectionTitle"><span>02</span><div><p className="eyebrow">Page roles</p><h2>題材頁與股票一覽的差別</h2></div></div>
          <div className="guideCompare"><article><h3>題材總覽</h3><p>回答「資金往哪個方向集中」。先比較大族群，再進細題材查看強度、廣度與相關股票。</p><Link href="/topics">依題材找方向</Link></article><article><h3>股票一覽</h3><p>回答「完整股票宇宙中，哪些股票符合目前條件」。列表保留價格、成交量與簡潔燈號，交易判讀集中在個股明細。</p><Link href="/watchlist">依條件找股票</Link></article></div>
        </section>

        <section className="guideSection" id="prices">
          <div className="guideSectionTitle"><span>03</span><div><p className="eyebrow">Price language</p><h2>四個價位如何使用</h2></div></div>
          <dl className="guideDefinitions">{priceTerms.map(([term, meaning]) => <div key={term}><dt>{term}</dt><dd>{meaning}</dd></div>)}</dl>
          <p className="guideNote">順序不是先找最低風險，而是先確認資料有效，再確認觀察資格與進場條件，最後檢查失效價是否能接受。</p>
        </section>

        <section className="guideSection" id="safety">
          <div className="guideSectionTitle"><span>04</span><div><p className="eyebrow">Safety gate</p><h2>這些狀態不能採取行動</h2></div></div>
          <ul className="guideWarnings"><li><strong>資料載入中或不可用</strong><span>等待重新載入成功，不使用上一個畫面的價格做判斷。</span></li><li><strong>資料過期</strong><span>延遲超過 freshness 契約時，只能追查資料來源，不能當作盤中價格。</span></li><li><strong>停牌或特殊狀態</strong><span>列表保留安全警示；個股明細會停止距觸發與交易判讀。</span></li><li><strong>缺少觸發價或失效價</strong><span>顯示資料不足，不以 0、文字價格或前端推算補值。</span></li></ul>
        </section>

        <section className="guideSection" id="filters">
          <div className="guideSectionTitle"><span>05</span><div><p className="eyebrow">Filters</p><h2>快速篩選與進階篩選</h2></div></div>
          <div className="guideCompare"><article><h3>快速篩選</h3><p>用趨勢偏多、接近突破、法人加碼、題材強勢與風險較低快速縮小範圍，適合每日掃描。</p></article><article><h3>進階篩選</h3><p>直接使用 snapshot 已提供的 MA、RS、MACD、KD、RSI、量價與法人欄位，適合驗證明確假設。缺資料不算符合。</p></article></div>
          <p className="guideNote">所有篩選只改變前端顯示範圍，不改變系統目前排序、正式分數、觀察資格或候選名單。</p>
        </section>
      </div>
    </main>
  );
}
