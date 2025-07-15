@echo off
ECHO [Direct FFMPEG Test]
ECHO =================================================================

REM IMPORTANT: Replace the path below with the full path to your ffmpeg.exe
SET FFMPEG_PATH="C:\path\to\your\ffmpeg\bin\ffmpeg.exe"

ECHO Combining 'shot_01.mp4' and 'shot_02.mp4' with 'main_theme.mp3'...

%FFMPEG_PATH% -i "output/final_film/shot_01.mp4" -i "output/final_film/shot_02.mp4" -i "output/final_film/main_theme.mp3" ^
-filter_complex "[0:v][1:v]concat=n=2:v=1[outv]" ^
-map "[outv]" -map 2:a -c:v libx264 -c:a aac -shortest "output/final_film/direct_ffmpeg_movie.mp4" -y

ECHO.
ECHO ✅ Test complete. Check for 'direct_ffmpeg_movie.mp4' in the output folder.
ECHO =================================================================
PAUSE