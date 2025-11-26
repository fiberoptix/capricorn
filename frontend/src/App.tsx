import React from 'react';
import { ThemeProvider } from './theme/ThemeProvider';
import { Layout } from './components/Layout';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Layout />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;

