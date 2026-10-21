import React from "react";
import { Gauge } from "lucide-react";

const Header: React.FC = () => {
  return (
    <header className="w-full py-6 px-4 md:px-8 text-center relative">
      <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-secondary-500/10 backdrop-blur-sm rounded-2xl"></div>
      <div className="relative">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary-400 to-secondary-400 rounded-full blur opacity-75 animate-pulse"></div>
            <Gauge className="w-8 h-8 text-white relative" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-300 to-secondary-300 bg-clip-text text-transparent">
            Prix<span className="text-primary-300">Pro</span>
          </h1>
        </div>
        <p className="text-gray-300 text-sm md:text-base max-w-md mx-auto">
          Estimation précise des prix de véhicules de luxe basée sur les
          spécifications détaillées
        </p>
      </div>
    </header>
  );
};

export default Header;
