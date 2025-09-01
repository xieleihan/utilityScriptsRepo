[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$dnsServers = @("8.8.8.8","1.1.1.1","223.5.5.5","114.114.114.114","119.29.29.29")

# Randomly select one domestic and one global domain
$global_domain = ( "www.google.com","www.facebook.com","www.youtube.com","www.twitter.com","www.instagram.com" | Get-Random )
$china_domain  = ( "www.baidu.com","www.taobao.com","www.jd.com","www.weibo.com","www.qq.com","www.bilibili.com" | Get-Random )

Write-Host "Test Domains: CN -> $china_domain  Global -> $global_domain" -ForegroundColor Yellow

foreach ($dns in $dnsServers) {
    foreach ($domain in @($global_domain,$china_domain)) {
        $times = @()
        for ($i=0; $i -lt 5; $i++) {
            $start = Get-Date
            Resolve-DnsName -Server $dns $domain | Out-Null
            $end = Get-Date
            $times += ($end - $start).TotalMilliseconds
        }
        $avg = ($times | Measure-Object -Average).Average
        Write-Host "$dns [$domain] -> Avg $([math]::Round($avg,2)) ms" -ForegroundColor Cyan
        
        # Get DNS resolution result
        $nslookup = nslookup $domain $dns
        Write-Host "Result:`n$nslookup" -ForegroundColor Gray
    }
}
