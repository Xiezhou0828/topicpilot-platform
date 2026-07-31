"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "今日" },
  { href: "/topics", label: "題材" },
  { href: "/watchlist", label: "股票一覽" },
  { href: "/favorites", label: "我的觀察" },
  { href: "/guide", label: "使用指南" },
  { href: "/studio", label: "AI工作室" },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <header className="rail" aria-label="題材領航導覽">
      <div className="railLeft">
        <Link className="railBrand" href="/">
          <strong>題材領航</strong>
          <span>Topic Pilot</span>
        </Link>
        <nav className="railLinks" aria-label="主要分頁">
          {links.map((link) => (
            <Link
              className={pathname === link.href ? "active" : ""}
              href={link.href}
              key={link.href}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="railUtility" aria-label="帳戶與訂閱區">
        <span>公開合成資料</span>
      </div>
    </header>
  );
}
