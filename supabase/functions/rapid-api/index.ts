import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

const NAME_MAP: Record<string, string> = {
  dietary_energy:    'calories',
  protein:           'protein_g',
  carbohydrates:     'carbs_g',
  total_fat:         'fat_g',
  weight_body_mass:  'body_mass_kg',
  resting_heart_rate:'resting_hr',
  step_count:         'steps',
  steps:              'steps',
  body_fat_percentage:'body_fat_pct',
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 })

  const body = await req.json()
  const metrics = body?.data?.metrics ?? []

  // DEBUG: store raw metric names so we can inspect them
  await supabase.from('health_debug').upsert({
    id: 1,
    received_at: new Date().toISOString(),
    metric_names: metrics.map((m: { name: string }) => m.name)
  })

  const byDate: Record<string, Record<string, number>> = {}

  for (const metric of metrics) {
    const col = NAME_MAP[metric.name]
    if (!col) continue
    for (const entry of metric.data ?? []) {
      const date = String(entry.date).slice(0, 10)
      if (!byDate[date]) byDate[date] = {}
      let val = entry.qty ?? entry.value ?? 0
      if (col === 'steps') val = Math.round(val * 1000)
      byDate[date][col] = val
    }
  }

  const rows = Object.entries(byDate).map(([date, vals]) => ({ date, ...vals }))

  if (rows.length === 0) {
    return new Response(JSON.stringify({
      inserted: 0,
      received_metrics: metrics.map((m: { name: string }) => m.name)
    }), { status: 200 })
  }

  const { error } = await supabase
    .from('apple_health_daily')
    .upsert(rows, { onConflict: 'date' })

  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  return new Response(JSON.stringify({
    inserted: rows.length,
    all_metric_names: metrics.map((m: { name: string }) => m.name)
  }), { status: 200 })
})
