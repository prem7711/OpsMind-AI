import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Upload", end: true },
  { to: "/history", label: "History" },
  { to: "/dashboard", label: "Dashboard" },
];

export function NavBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-white/10 bg-[#0b0c10]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-lg shadow-indigo-500/30">
            S
          </div>
          <span className="text-base font-semibold text-slate-100">Sentinel AI</span>
        </div>
        <nav className="flex items-center gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
