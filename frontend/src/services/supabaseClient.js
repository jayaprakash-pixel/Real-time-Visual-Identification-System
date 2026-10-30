// One shared Supabase client for the whole app.
import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !key) {
  // eslint-disable-next-line no-console
  console.warn('Supabase env vars missing: set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env');
}

export const supabase = createClient(url, key);

// Normalized error used by all pages: { status, message, field? }
export function fail(status, message, field) {
  return Object.assign(new Error(message), { status, message, field });
}
