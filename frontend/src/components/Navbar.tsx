import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, User, Crown, Menu, Sparkles } from 'lucide-react';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-xl border-b border-white/10">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white p-2 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
              <Crown className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Coach de Empleo IA
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-gray-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Dashboard
                </Link>
                <Link
                  to="/cv-editor"
                  className="text-gray-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Editor de CV
                </Link>
                <Link
                  to="/cover-letter"
                  className="text-gray-300 hover:text-white transition-colors flex items-center px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Cartas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-400" />}
                </Link>
                <Link
                  to="/interview"
                  className="text-gray-300 hover:text-white transition-colors flex items-center px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Entrevistas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-400" />}
                </Link>
                
                {/* User Menu */}
                <div className="flex items-center space-x-4">
                  {user.is_premium && (
                    <span className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 px-3 py-1 rounded-full text-xs font-bold flex items-center shadow-lg">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Premium
                    </span>
                  )}
                  <div className="flex items-center space-x-2 text-gray-300">
                    <User className="w-5 h-5" />
                    <span>{user.full_name}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-1 text-gray-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-red-500/20"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Salir</span>
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  to="/pricing"
                  className="text-gray-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Precios
                </Link>
                <Link
                  to="/login"
                  className="text-gray-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Iniciar Sesión
                </Link>
                <Link
                  to="/register"
                  className="bg-gradient-to-r from-red-500 to-pink-500 text-white px-6 py-2 rounded-xl font-semibold hover:shadow-lg hover:shadow-red-500/25 transition-all duration-300 transform hover:scale-105"
                >
                  Registrarse
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-300 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
            >
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 border-t border-white/10 mt-4 pt-4">
            <div className="flex flex-col space-y-2">
              {user ? (
                <>
                  <Link
                    to="/dashboard"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/cv-editor"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Editor de CV
                  </Link>
                  <Link
                    to="/cover-letter"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10 flex items-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Cartas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-400" />}
                  </Link>
                  <Link
                    to="/interview"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10 flex items-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Entrevistas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-400" />}
                  </Link>
                  {user.is_premium && (
                    <div className="px-4 py-2">
                      <span className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 px-3 py-1 rounded-full text-xs font-bold flex items-center w-fit">
                        <Sparkles className="w-3 h-3 mr-1" />
                        Premium
                      </span>
                    </div>
                  )}
                  <button
                    onClick={handleLogout}
                    className="text-left text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-red-500/20 flex items-center"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Salir
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/pricing"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Precios
                  </Link>
                  <Link
                    to="/login"
                    className="text-gray-300 hover:text-white transition-colors py-3 px-4 rounded-lg hover:bg-white/10"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Iniciar Sesión
                  </Link>
                  <Link
                    to="/register"
                    className="bg-gradient-to-r from-red-500 to-pink-500 text-white px-6 py-3 rounded-xl font-semibold text-center mx-4 mt-2 hover:shadow-lg hover:shadow-red-500/25 transition-all duration-300"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Registrarse
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;