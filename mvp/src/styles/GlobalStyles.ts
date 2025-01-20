// src/styles/GlobalStyles.ts
import { createGlobalStyle } from 'styled-components';
import { Theme } from '../types/theme';

export const GlobalStyles = createGlobalStyle<{ theme: Theme }>`
  :root {
    --db-primary: ${({ theme }) => theme.primary};
    --db-accent1: ${({ theme }) => theme.accent1};
    --db-accent2: ${({ theme }) => theme.accent2};
    --db-surface: ${({ theme }) => theme.surface};
    --db-text: ${({ theme }) => theme.text};
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    background: ${({ theme }) => theme.gradientMain};
    color: ${({ theme }) => theme.text};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  .glass-card {
    background: ${({ theme }) => theme.gradientSurface};
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 1.5rem;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
  }
`;