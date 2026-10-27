# make_speech_wav.ps1: two speech wavs for the bridge's /hear selftest, from this PC's own voice, offline.
#
# Why a script in the repo: tools/ai_bridge.py --selftest sends a wav to /hear and prints the transcript, and a
# judge needs a way to produce that wav without a network, a model, or a recording. System.Speech ships with
# Windows and speaks locally, and the format is what the bridge's whisper worker wants: 16000 Hz, 16 bit, mono.
#
# Writes into <repo>\output\ai_bridge\ (gitignored), then say:
#     python tools\ai_bridge.py --selftest --wav output\ai_bridge\selftest_speech_two.wav

Add-Type -AssemblyName System.Speech
$out = Join-Path (Split-Path -Parent $PSScriptRoot) 'output\ai_bridge'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
    16000,
    [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono)

$first = Join-Path $out 'selftest_speech.wav'
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile($first, $format)
$synth.Speak('You have been standing on watch all night, sailor. Take a break, I will cover for you.')
$synth.Dispose()

$second = Join-Path $out 'selftest_speech_two.wav'
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile($second, $format)
$synth.Speak('The watch is long and the swell is getting worse. Nobody has relieved me since midnight.')
$synth.Dispose()

foreach ($path in @($first, $second)) {
    $item = Get-Item $path
    Write-Output ("wrote {0} ({1} bytes)" -f $item.FullName, $item.Length)
}
