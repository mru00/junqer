#!/bin/bash -e

trap '{echo "some error occured, stopping."; exit 1;}' ERR

# create sample series file structure
# mru, 2011-01

# sudo apt-get install mjpegtools

SHOW="super show"
nseasons=4
nepisodes=10
nframes=10

gen_image() {
  text="$1"
  for i in `seq -w 0 $((nframes-1))`; do

    pos=$(( 20 + i*500/($nframes-1) ))
  convert -size 640x160 xc:black \
    -quality 100 \
    -pointsize 32 \
    -font ../DS-DIGI.TTF \
    -fill white\
    -stroke white \
    -draw "text 20,55 '$text'" \
    -draw "rectangle 15,100 535,150" \
    -fill black -draw "rectangle 20,110 $pos,140" \
    "ep$i.jpg"
done
}

gen_movie() {
  outfile="$1"
  jpeg2yuv -v 0 -I p -f 8 -j "ep%01d.jpg"| yuv2lav -f a -b 10000 -o "$outfile"
}


for i in `seq -w $nseasons`; do

  season="season $i"
  mkdir -p "$SHOW/$season"

  for j in `seq -w $nepisodes`; do
    episode="episode $j"
    gen_image "$SHOW - $season - $episode"
    gen_movie "$SHOW/$season/$episode.avi"
  done
done
