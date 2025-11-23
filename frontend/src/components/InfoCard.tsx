import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface InfoCardProps {
  deviceCount: number
  mounted: boolean
}

export function InfoCard({ deviceCount, mounted }: InfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Info</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between py-2 border-b">
          <span className="text-sm text-muted-foreground">Total Devices</span>
          <span className="font-semibold">{deviceCount}</span>
        </div>
        <div className="flex items-center justify-between py-2 border-b">
          <span className="text-sm text-muted-foreground">Mounted</span>
          <span className="font-semibold text-green-600">{mounted ? 1 : 0}</span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-muted-foreground">Status</span>
          <Badge variant="secondary">{mounted ? 'Active' : 'Idle'}</Badge>
        </div>
      </CardContent>
    </Card>
  )
}
