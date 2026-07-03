$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
  Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
  })[0]

function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait() | Out-Null
  if ($netTask.Exception) {
    throw $netTask.Exception
  }
  $netTask.Result
}

[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapPixelFormat, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapAlphaMode, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
  throw 'Windows OCR engine is not available.'
}

$inputs = @()
$pageDir = if (Test-Path -LiteralPath 'extracted_pages_200') { 'extracted_pages_200' } else { 'extracted_pages' }
$inputs += Get-ChildItem -Path $pageDir -Filter '*.png' | Sort-Object Name
$inputs += Get-Item -LiteralPath 'QUIZ 11.png'
$inputs += Get-Item -LiteralPath 'QUIZ 12.png'

$pages = foreach ($inputFile in $inputs) {
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($inputFile.FullName)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await ($decoder.GetSoftwareBitmapAsync([Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8, [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied)) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

  $lines = foreach ($line in $result.Lines) {
    $words = @($line.Words)
    $left = ($words | ForEach-Object { $_.BoundingRect.X } | Measure-Object -Minimum).Minimum
    $top = ($words | ForEach-Object { $_.BoundingRect.Y } | Measure-Object -Minimum).Minimum
    $right = ($words | ForEach-Object { $_.BoundingRect.X + $_.BoundingRect.Width } | Measure-Object -Maximum).Maximum
    $bottom = ($words | ForEach-Object { $_.BoundingRect.Y + $_.BoundingRect.Height } | Measure-Object -Maximum).Maximum

    [pscustomobject]@{
      text = $line.Text
      x = [math]::Round($left, 2)
      y = [math]::Round($top, 2)
      width = [math]::Round($right - $left, 2)
      height = [math]::Round($bottom - $top, 2)
      words = @($words | ForEach-Object {
        [pscustomobject]@{
          text = $_.Text
          x = [math]::Round($_.BoundingRect.X, 2)
          y = [math]::Round($_.BoundingRect.Y, 2)
          width = [math]::Round($_.BoundingRect.Width, 2)
          height = [math]::Round($_.BoundingRect.Height, 2)
        }
      })
    }
  }

  [pscustomobject]@{
    file = $inputFile.Name
    path = $inputFile.FullName
    width = $bitmap.PixelWidth
    height = $bitmap.PixelHeight
    text = $result.Text
    lines = @($lines)
  }
}

$pages | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'ocr_lines.json' -Encoding UTF8
