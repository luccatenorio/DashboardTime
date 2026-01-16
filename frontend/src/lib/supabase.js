import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://lsxrqbzitmbyycfxtpyu.supabase.co'
// Using Service Role Key to bypass RLS policies on localhost
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzeHJxYnppdG1ieXljZnh0cHl1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY2NDIwNywiZXhwIjoyMDgzMjQwMjA3fQ.o7Tcs0jJ-cj6Qwyo1fA4BQ0tJpEfiOnzcAt77YKsVTE'

export const supabase = createClient(supabaseUrl, supabaseKey)
