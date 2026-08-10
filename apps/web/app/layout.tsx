import type { Metadata, Viewport } from "next";
import "./globals.css";
import { SnapshotProvider } from "./lib/snapshot-store";

export const metadata: Metadata = {
  title: "題材領航｜題材資金流向儀表",
  description: "TopicPilot 原版前端與企業資料管線的公開合成資料展示。",
  openGraph: {
    title: "題材領航｜題材資金流向儀表",
    description: "保留原版前端，資料由 FastAPI／PostgreSQL read model 提供。",
    type: "website",
    images: ["/og-topic-pilot.png"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "");
  const snapshotApiUrl = process.env.NEXT_PUBLIC_SNAPSHOT_API_URL?.trim()
    || (apiBaseUrl ? `${apiBaseUrl}/api/v1/snapshot/latest` : undefined);

  return (
    <html lang="zh-Hant" data-snapshot-api-url={snapshotApiUrl} data-api-base-url={apiBaseUrl}>
      <body>
        <SnapshotProvider>{children}</SnapshotProvider>
      </body>
    </html>
  );
}
