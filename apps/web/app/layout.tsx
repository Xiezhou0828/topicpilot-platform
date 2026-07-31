import type { Metadata } from "next";
import { AppFrame } from "./components/AppFrame";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://topicpilot-platform.game0962046460.chatgpt.site"),
  title: {
    default: "TopicPilot Platform｜金融資料研究工作台",
    template: "%s｜TopicPilot Platform",
  },
  description:
    "以 PostgreSQL、FastAPI 與 React 打造的金融資料 read platform 公開展示，呈現資料血緣、題材輪動與策略研究流程。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: {
    type: "website",
    locale: "zh_TW",
    siteName: "TopicPilot Platform",
    title: "TopicPilot Platform｜從市場資料到可驗證的研究流程",
    description: "一套以 API contract、資料品質與可重現分析為核心的金融資料產品。",
    images: [
      {
        url: "/og.png",
        width: 1731,
        height: 909,
        alt: "TopicPilot Platform enterprise read model",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TopicPilot Platform",
    description: "Financial data read platform · PostgreSQL · FastAPI · React",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body><AppFrame>{children}</AppFrame></body>
    </html>
  );
}
