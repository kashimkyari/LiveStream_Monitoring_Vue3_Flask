#!/bin/bash
deployments=(
# New list (20 deployments)
  "https://jetcamstudios-czfcrpu5u-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-cxllbxsej-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-fh9i69ibd-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-a8ph9s4te-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-kiimhoiwy-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-32p17l0q1-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-rhpy95mz2-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-8drst46yg-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-psztye6gr-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-qd6nwzxpl-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-1la0hbg98-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-g2wxvek4q-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-b1qgwyk7t-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-c8gykghxr-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-20bzkw8x7-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-e1vmlo0hk-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-drg3jashj-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-r9bt0zw2j-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-rao6xgq26-kashimkyaris-projects.vercel.app"
  "https://jetcamstudios-1yggqmjwa-kashimkyaris-projects.vercel.app"

)
for deployment in "${deployments[@]}"; do
  vercel rm "$deployment" -y
  echo "Deleted $deployment"
done
