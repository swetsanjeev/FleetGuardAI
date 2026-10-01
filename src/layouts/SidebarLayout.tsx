import React from "react";

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  return <div className="with-sidebar"><aside>{/* links */}</aside><main>{children}</main></div>;
}
