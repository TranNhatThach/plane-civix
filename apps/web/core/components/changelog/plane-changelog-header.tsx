import React from "react";
import { Link } from "react-router";

export const PlaneChangelogHeader: React.FC = () => {
  return (
    <header className="border-custom-border-200/80 bg-custom-background-100/95 sticky top-0 z-50 w-full border-b backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-90">
            {/* Plane Official Logo Mark */}
            <svg
              className="text-custom-text-100 h-6 w-6"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
              <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
            </svg>
            <span className="text-lg text-custom-text-100 font-bold tracking-tight">Plane</span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              to="/civix"
              className="text-sm text-custom-text-200 hover:text-custom-text-100 font-medium transition-colors"
            >
              Product
            </Link>
            <Link
              to="/civix"
              className="text-sm text-custom-text-200 hover:text-custom-text-100 font-medium transition-colors"
            >
              Solutions
            </Link>
            <Link to="/changelog" className="text-sm text-custom-primary-100 font-semibold transition-colors">
              Resources
            </Link>
            <Link
              to="/civix"
              className="text-sm text-custom-text-200 hover:text-custom-text-100 font-medium transition-colors"
            >
              Pricing
            </Link>
            <Link
              to="/god-mode"
              className="text-sm text-custom-text-200 hover:text-custom-text-100 font-medium transition-colors"
            >
              Self-host Plane
            </Link>
          </nav>
        </div>

        {/* Right CTA Links */}
        <div className="flex items-center gap-4">
          <Link
            to="/civix"
            className="text-sm text-custom-text-200 hover:text-custom-text-100 hidden font-medium transition-colors sm:block"
          >
            Contact sales
          </Link>
          <Link
            to="/"
            className="text-sm text-custom-text-200 hover:text-custom-text-100 font-medium transition-colors"
          >
            Login
          </Link>
          <Link
            to="/"
            className="bg-custom-text-100 text-xs sm:text-sm text-custom-background-100 shadow-sm inline-flex items-center justify-center rounded-lg px-4 py-2 font-semibold transition-all hover:opacity-90 active:scale-95"
          >
            Get started free
          </Link>
        </div>
      </div>
    </header>
  );
};
