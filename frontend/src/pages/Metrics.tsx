import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function Metrics() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Metrics Guide</h1>
        <p className="text-muted-foreground">Understanding your training metrics</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>TSS (Training Stress Score)</CardTitle>
            <CardDescription>Quantifies the training load of a workout</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              TSS represents the overall stress of a workout. A value of 100 roughly equals one hour
              at threshold intensity.
            </p>
            <h4>Calculation Methods:</h4>
            <ul>
              <li><strong>Power-based (cycling)</strong>: Uses normalized power and FTP</li>
              <li><strong>HR-based</strong>: Uses heart rate reserve and LTHR</li>
              <li><strong>Pace-based (running)</strong>: Uses pace relative to threshold pace</li>
              <li><strong>Duration fallback</strong>: Estimates based on duration and activity type</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>CTL (Chronic Training Load)</CardTitle>
            <CardDescription>Your fitness level</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              CTL is a 42-day exponentially weighted average of your daily TSS. It represents your
              accumulated fitness or "base" fitness level.
            </p>
            <p>
              A higher CTL means you've consistently trained at higher loads over the past several weeks.
              It typically takes 4-6 weeks of consistent training to significantly move CTL.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ATL (Acute Training Load)</CardTitle>
            <CardDescription>Your recent fatigue</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              ATL is a 7-day exponentially weighted average of your daily TSS. It represents your
              recent training load or "fatigue".
            </p>
            <p>
              ATL responds quickly to changes in training. A sudden increase in training will
              spike ATL, indicating accumulated fatigue.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>TSB (Training Stress Balance)</CardTitle>
            <CardDescription>Your form / readiness</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              TSB = CTL - ATL. It represents the balance between your fitness and fatigue.
            </p>
            <h4>Form Zones:</h4>
            <ul>
              <li><strong>Fresh (5 to 25)</strong>: Well-rested, good for key workouts or races</li>
              <li><strong>Neutral (-10 to 5)</strong>: Balanced training state</li>
              <li><strong>Tired (-30 to -10)</strong>: Accumulated fatigue, training hard</li>
              <li><strong>Exhausted (&lt; -30)</strong>: Risk of overtraining, consider rest</li>
              <li><strong>Transition (&gt; 25)</strong>: Losing fitness, may need more training</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Intensity Factor (IF)</CardTitle>
            <CardDescription>Relative intensity of a workout</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              IF is the ratio of your workout intensity to your threshold intensity:
            </p>
            <ul>
              <li><strong>Power</strong>: Normalized Power / FTP</li>
              <li><strong>HR</strong>: Average HR / LTHR</li>
              <li><strong>Pace</strong>: Threshold Pace / Actual Pace</li>
            </ul>
            <p>
              IF = 1.0 means you performed at threshold. Values above 1.0 indicate supra-threshold effort.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Thresholds</CardTitle>
            <CardDescription>Your personal benchmark values</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <ul>
              <li><strong>FTP</strong>: Functional Threshold Power - max power for ~1 hour</li>
              <li><strong>LTHR</strong>: Lactate Threshold HR - HR at threshold intensity</li>
              <li><strong>Max HR</strong>: Maximum heart rate achieved</li>
              <li><strong>Threshold Pace</strong>: Pace you can sustain for ~1 hour</li>
            </ul>
            <p>
              Accurate thresholds are essential for meaningful TSS calculations.
              Update them as your fitness changes.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ACWR (Acute:Chronic Workload Ratio)</CardTitle>
            <CardDescription>Injury risk indicator</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              ACWR = ATL / CTL. It compares your recent training load to your long-term fitness,
              helping identify injury risk from training spikes.
            </p>
            <h4>Risk Zones:</h4>
            <ul>
              <li><strong>Undertrained (&lt; 0.8)</strong>: Training may be too light to maintain fitness</li>
              <li><strong>Optimal (0.8 to 1.3)</strong>: Sweet spot for progressive adaptation</li>
              <li><strong>Caution (1.3 to 1.5)</strong>: Elevated injury risk, monitor recovery</li>
              <li><strong>Danger (&gt; 1.5)</strong>: High injury risk, consider reducing load</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Monotony</CardTitle>
            <CardDescription>Training variation measure</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              Monotony measures how repetitive your training is over a 7-day period.
              It's calculated as: Average Daily TSS / Standard Deviation of Daily TSS.
            </p>
            <h4>Guidelines:</h4>
            <ul>
              <li><strong>&lt; 1.5</strong>: Good variation in training</li>
              <li><strong>1.5 to 2.0</strong>: Moderate - consider varying intensity</li>
              <li><strong>&gt; 2.0</strong>: High monotony - increase training variety to reduce overtraining risk</li>
            </ul>
            <p>
              High monotony combined with high training load increases risk of overtraining and illness.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Strain</CardTitle>
            <CardDescription>Overall training stress indicator</CardDescription>
          </CardHeader>
          <CardContent className="prose prose-sm dark:prose-invert">
            <p>
              Strain = Weekly TSS x Monotony. It combines training volume with training pattern
              to give an overall stress indicator.
            </p>
            <h4>Guidelines:</h4>
            <ul>
              <li><strong>&lt; 2000</strong>: Low strain, sustainable training</li>
              <li><strong>2000 to 4000</strong>: Moderate strain, normal training block</li>
              <li><strong>4000 to 6000</strong>: High strain, ensure adequate recovery</li>
              <li><strong>&gt; 6000</strong>: Very high strain, increased illness and overtraining risk</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
