import type { Metadata } from "next";
import { DataStatusView } from "../views/DataStatusView";

export const metadata: Metadata = { title: "系統架構" };

export default function ArchitecturePage() { return <DataStatusView />; }
