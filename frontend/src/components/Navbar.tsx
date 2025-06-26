import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, User, Crown, Menu } from 'lucide-react';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-lg border-b-2 border-peru-red">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="bg-peru-red text-white p-2 rounded-lg">
              <Crown className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold text-gray-800">
              Coach de Empleo IA
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-gray-600 hover:text-peru-red transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/cv-editor"
                  className="text-gray-600 hover:text-peru-red transition-colors"
                >
                  Editor de CV
                </Link>
                <Link
                  to="/cover-letter"
                  className="text-gray-600 hover:text-peru-red transition-colors flex items-center"
                >
                  Cartas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-500" />}
                </Link>
                <Link
                  to="/interview"
                  className="text-gray-600 hover:text-peru-red transition-colors flex items-center"
                >
                  Entrevistas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-500" />}
                </Link>
                
                {/* User Menu */}
                <div className="flex items-center space-x-4">
                  {user.is_premium && (
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium flex items-center">
                      <Crown className="w-3 h-3 mr-1" />
                      Premium
                    </span>
                  )}
                  <div className="flex items-center space-x-2">
                    <User className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-700">{user.full_name}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-1 text-gray-600 hover:text-peru-red transition-colors"
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
                  className="text-gray-600 hover:text-peru-red transition-colors"
                >
                  Precios
                </Link>
                <Link
                  to="/login"
                  className="text-gray-600 hover:text-peru-red transition-colors"
                >
                  Iniciar Sesión
                </Link>
                <Link
                  to="/register"
                  className="bg-peru-red text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
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
              className="text-gray-600 hover:text-peru-red transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden pb-4">
            <div className="flex flex-col space-y-2">
              {user ? (
                <>
                  <Link
                    to="/dashboard"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/cv-editor"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Editor de CV
                  </Link>
                  <Link
                    to="/cover-letter"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2 flex items-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Cartas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-500" />}
                  </Link>
                  <Link
                    to="/interview"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2 flex items-center"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Entrevistas {!user.is_premium && <Crown className="w-4 h-4 ml-1 text-yellow-500" />}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="text-left text-gray-600 hover:text-peru-red transition-colors py-2 flex items-center"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Salir
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/pricing"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Precios
                  </Link>
                  <Link
                    to="/login"
                    className="text-gray-600 hover:text-peru-red transition-colors py-2"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Iniciar Sesión
                  </Link>
                  <Link
                    to="/register"
                    className="bg-peru-red text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-center"
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