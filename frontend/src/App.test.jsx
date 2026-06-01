import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

describe('App Component', () => {
  it('renders the main dashboard interface', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    )

    // Verify main header exists
    const headings = screen.getAllByText(/Social/i)
    expect(headings.length).toBeGreaterThan(0)
    expect(screen.getByText(/Analyzer/i)).toBeInTheDocument()

    // Verify the search input exists
    const input = screen.getByPlaceholderText('URL profilo o username...')
    expect(input).toBeInTheDocument()

    // Verify the submit button exists
    const button = screen.getByRole('button', { name: /Scansiona/i })
    expect(button).toBeInTheDocument()
    
    // Verifica la sezione configurazione
    expect(screen.getByText('Configurazione Sensori')).toBeInTheDocument()
  })
})
