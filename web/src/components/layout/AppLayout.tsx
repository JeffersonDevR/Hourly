import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-mh-canvas text-mh-text">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="mx-auto w-full max-w-[1440px] flex-1 px-8 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
