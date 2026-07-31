import type { Metadata } from "next";
import { DataStatusView } from "../views/DataStatusView";

export const metadata: Metadata = { title: "資料平台與架構" };

export default function DataStatusPage() { return <DataStatusView />; }
