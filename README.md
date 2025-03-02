# AI Powered Content Farm

There is a good chance you've seen a story time video lazily pasted over some subway surfer gameplay on your social media feed in the last year. Maybe it looked something like this:

https://www.youtube.com/shorts/tBPltTm_wJ0

One day I was sucked in wasting time watching one of these souless videos. That is when it dawned on me I could recreate these videos with even less effort!

This project uses Open-AIs GPT 4.0 mini to generate fake stories which are then voiced over by Open-AIs Dall-e 3 TTS. This audio is then complied with this audio using https://github.com/strob/gentle to align the audio with the text. My paticular implementation relied on Docker, however this project could easily be modified to use a local implementation of Gentle. Finally using MoviePY the text is put over a background video with some copy right free music.

Sound familiar? Thats right, the video I linked at the top of this read me was made using my program.
