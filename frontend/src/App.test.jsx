import { render, screen } from '@testing-library/react'; import { MemoryRouter } from 'react-router-dom'
import { test, expect } from 'vitest'; import Login from './pages/Login'
test('login form renders', () => { render(<MemoryRouter><Login /></MemoryRouter>); expect(screen.getByRole('heading', { name: 'Log in' })).toBeTruthy() })
