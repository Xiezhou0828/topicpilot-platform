"use client";

import {
  Activity,
  Blocks,
  Database,
  Layers3,
  LayoutDashboard,
  Menu,
  Network,
  ShieldCheck,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const navigation = [
  { href: "/", label: "總覽", hint: "Overview", icon: LayoutDashboard },
  { href: "/stocks", label: "股票宇宙", hint: "Stocks", icon: Activity },
  { href: "/topics", label: "題材輪動", hint: "Topics", icon: Layers3 },
  { href: "/strategies", label: "策略實驗室", hint: "Strategies", icon: Blocks },
  { href: "/data-status", label: "資料平台", hint: "Data platform", icon: Database },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function AppFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">跳至主要內容</a>
      <header className="mobile-header">
        <Link className="brand-lockup compact" href="/" aria-label="TopicPilot Platform 首頁">
          <span className="brand-mark" aria-hidden="true"><Network size={18} /></span>
          <span><strong>TopicPilot</strong><small>DATA PLATFORM</small></span>
        </Link>
        <button
          className="menu-button"
          type="button"
          aria-label={menuOpen ? "關閉導覽選單" : "開啟導覽選單"}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((value) => !value)}
        >
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </header>

      <aside className={`side-rail ${menuOpen ? "open" : ""}`} aria-label="主要導覽">
        <Link className="brand-lockup" href="/" aria-label="TopicPilot Platform 首頁">
          <span className="brand-mark" aria-hidden="true"><Network size={20} /></span>
          <span><strong>TopicPilot</strong><small>DATA PLATFORM</small></span>
        </Link>
        <div className="rail-context">
          <span>PUBLIC CASE STUDY</span>
          <p>Financial intelligence<br />read platform</p>
        </div>
        <nav id="primary-navigation" className="primary-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(pathname, item.href);
            return (
              <Link href={item.href} key={item.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined} onClick={() => setMenuOpen(false)}>
                <Icon size={18} aria-hidden="true" />
                <span><strong>{item.label}</strong><small>{item.hint}</small></span>
              </Link>
            );
          })}
        </nav>
        <div className="rail-stack" aria-label="技術架構">
          <div><span>01</span><p>PostgreSQL</p></div>
          <div><span>02</span><p>FastAPI</p></div>
          <div><span>03</span><p>React</p></div>
        </div>
        <div className="rail-footer"><ShieldCheck size={16} aria-hidden="true" /><span>Read-only architecture</span></div>
      </aside>

      {menuOpen && <button className="nav-scrim" aria-label="關閉導覽選單" type="button" onClick={() => setMenuOpen(false)} />}

      <div className="content-column">
        <div className="demo-banner" role="note">
          <span className="demo-dot" aria-hidden="true" />
          <strong>展示資料・非投資建議</strong>
          <span>所有名稱與數值均為匿名合成資料</span>
        </div>
        <main id="main-content" tabIndex={-1}>{children}</main>
        <footer className="site-footer">
          <span>TopicPilot Platform</span>
          <span>Public portfolio · Read-only · Synthetic data</span>
        </footer>
      </div>
    </div>
  );
}
