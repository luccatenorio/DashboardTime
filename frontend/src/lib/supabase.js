import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://atlrypolvbxlfozfnujv.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF0bHJ5cG9sdmJ4bGZvemZudWp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4OTIzMDgsImV4cCI6MjA5MjQ2ODMwOH0.q6oYilF6LIaYCYN2gNT-Y81J0oxMhfP8YVwO-ZDIThI'

export const supabase = createClient(supabaseUrl, supabaseKey)
