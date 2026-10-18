# Job

- Person: An unnamed viewer. CuratorAI does not name a person; the Home screen addresses someone choosing videos to watch.
- Situation: They have opened the local three-video demo and want to choose something to watch.
- Arrival kind: Finish a job.
- Job: Find and start a video to watch.
- Done: A selected video plays and its playback time advances.
- Leave: They cannot identify something to watch, or the selected video never plays and offers no recovery.
- Path: Home → Watch Now → watch page → Home / Continue Watching → watch page again → Explore → ColdFusion → Search → close and reopen Home.
- Stages this product does not have: Account creation, checkout, publishing, and export. Subscriptions and viewing history are simulated in this browser.
- Source: Watched Home at http://localhost:3000/ on the local branch codex/pr16-pixeltable-latest. The screen shows “CuratorAI,” “Watch Now,” “More Info,” “Recently Added,” and “Deep Dives.” Read src/app/page.tsx and src/lib/user-state.tsx for the intended return path and browser persistence. The viewer and situation are inferred from these product surfaces, not an observed customer interview.
