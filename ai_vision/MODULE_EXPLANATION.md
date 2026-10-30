# AI Vision & Recognition Module — Explained Simply

## 1. What is the whole project?

A **real-time missing person detection system**.

- A **phone or CCTV camera** watches an area and sends live video to a **laptop**.
- The police/operator **registers a missing person once** with their photo.
- The AI on the laptop **watches the live video continuously**. When that person appears, it **confirms the match over several frames**, **saves a photo of the whole scene**, and **raises an alert**.

The project has 3 parts (one per team member):

| Member | Part | Job |
|---|---|---|
| Member 1 | Registration & Database | Login, register missing person details and photo |
| **Member 2** | **AI Vision & Recognition (this module)** | **Find faces in the live video and recognise the missing person** |
| Member 3 | Alerts & Dashboard | Popup/sound alert, detection history screen |

---

## 2. What does our module do, in one line?

> **It takes live video, finds every face, and decides — reliably — whether any face belongs to a registered missing person.**

---

## 3. The flow (step by step)

```
 Phone / CCTV / Webcam
        |
 [US-01] Take the newest frame only (low latency)
        |
 [US-02] Find faces (YuNet) -> straighten face -> convert face to 128 numbers (SFace)
        |
 [US-03] Give each face an ID and follow it across frames (tracking)
        |
 [US-04] Skip bad faces (blurry/dark/side) and don't recognise every frame (saves time)
        |
 [US-05] Registered missing persons are kept ready as numbers in memory
        |
 [US-06] Compare live face numbers with registered face numbers (similarity score)
        |
 [US-07] Score above 0.363? -> possible match
        |
 [US-08] Same person matched in 3 of the last 5 checks? -> CONFIRMED
        |
 [US-09] Where is the person in the picture? (position / zone)
        |
 [US-10] Save the full scene photo + face photo + details as evidence
        |
 [US-11] Send the result to Member 3's alert system
        |
 [US-12] All detections can be searched later (history)
```

---

## 4. Each step in simple words

### US-01 — Low-latency camera feed
The camera gives ~30 frames per second, but the AI can process fewer. If we queued every frame, the AI would fall behind and look at **old** video.
So we keep **only the newest frame** in a "latest-frame buffer" (capacity 1). The camera runs in its own **thread** and keeps replacing the frame; the AI always takes the freshest one.
**Why:** for surveillance, *what is happening now* matters more than processing every frame.

### US-02 — Face detection and feature extraction
- **YuNet** (a small, fast face-detection model) finds all faces and gives **5 landmarks**: two eyes, nose, two mouth corners.
- **Alignment:** using those 5 points we rotate/scale the face into a standard straight **112×112** image. A tilted face becomes a straight face.
- **SFace** (face-recognition model) turns the aligned face into **128 numbers** called an **embedding** — like a "fingerprint" of the face.
**Why embeddings:** comparing 128 numbers is much faster and more reliable than comparing raw images.

### US-03 — Face tracking
Detection only says "there are 3 faces". It doesn't know that the face in this frame is the **same** person as in the previous frame.
The tracker gives each face a **Track ID** (#1, #2…) by matching each face to the nearest face position from the previous frame (centre distance). Nearest pairs are matched first so two people walking side by side don't swap IDs.
**Why:** so we can say *"the same person"* matched across many frames.

### US-04 — Selective recognition + quality check
- Running SFace on every face in every frame is wasteful. We recognise a tracked face **on its first frame, then every 10 frames** — and **every 2 frames** when it might be a match (to confirm faster).
- Before recognising, a **quality check** skips faces that are **too small, blurry, too dark/bright, or turned too much sideways**, because those give wrong results.
**Why:** keeps the system real-time and avoids bad guesses.

### US-05 — Reference management (registered persons)
When a missing person is registered, their photo is converted to an embedding **once** and saved (`data/references.npz`). At start-up all embeddings are loaded into memory.
- Several photos per person are supported (we capture **5 poses**: straight, left, right, up, down).
- We also store a **mirror image** of each photo, so "turned left" also covers "turned right".
**Why:** the live system never re-processes the photos; matching is instant.

### US-06 — Comparing faces
We compare the live embedding with every registered embedding using **cosine similarity**:
- close to **1** → very similar faces
- around **0** → different people
All registered persons are compared in a single matrix calculation, so even hundreds of persons are fast.

### US-07 — Match decision
If the best score is **≥ 0.363**, it is a *possible* match. (0.363 is the threshold published for the SFace model, and our tests confirmed it.)

### US-08 — Multi-frame verification
One frame can be wrong (bad angle, lighting). So we **never** confirm from a single frame.
A match is **confirmed only when the same Track ID matches the same person in 3 of the last 5 checks, with an average score ≥ 0.40**.
**Why:** removes false alarms — a stranger who looks similar for one frame won't trigger an alert.

### US-09 — Location
We record **where** the person is in the image: the box coordinates, the centre point, and a simple zone such as *"top-left"* or *"middle-center"*.

### US-10 — Evidence capture
On a confirmed match we save:
- the **full camera frame** with the person boxed in red, camera ID and time (shows surroundings, people nearby, direction),
- the **face crop**,
- a **record line** (who, score, time, camera, location, image paths) in `detections.jsonl`.

### US-11 — Real-time notification (hand-off)
The confirmed result is passed to **Member 3's alert system** through one function (`on_match`). Our side also shows a red **MATCH** banner on screen and prints the details. The same person is not re-alerted within 30 seconds (no spam).

### US-12 — Detection history
All saved detections can be searched by **person, camera, or date** (`us-12/detection_history.py`).

---

## 5. Technologies used

| Thing | What we used | Why |
|---|---|---|
| Language | Python | Easy, strong AI/vision libraries |
| Vision library | OpenCV | Camera, image processing, runs the AI models |
| Face detector | **YuNet** (ONNX model) | Fast on a normal laptop CPU, gives 5 landmarks |
| Face recogniser | **SFace** (ONNX model) | Accurate, produces 128-number embeddings |
| Comparison | Cosine similarity (NumPy) | Standard for face embeddings |
| Phone as camera | IP Webcam app (MJPEG over Wi-Fi) | Simple, no extra hardware |

No GPU or internet is needed — everything runs locally on the laptop.

---

## 6. Test results (what we actually measured)

| Test | Result |
|---|---|
| Same person, two different photos | score **0.69** → MATCH |
| Two different people | score **≈ 0.0** → NO MATCH |
| 15-face crowd photo vs registered persons | highest **0.20** → no false match |
| Full pipeline on test video (2 registered people + a crowd) | both confirmed after 3 frames, **no false alarm** |
| Live webcam test | own face recognised and confirmed |
| Quality check | correctly rejects blurry, dark, tiny and side-turned faces |

---

## 7. Questions professors may ask (and answers)

**Q: Why not just compare the photo with the camera image directly?**
Raw images change with light, size and position. Embeddings capture *facial features*, so the same person gives similar numbers even when the picture is different.

**Q: Why do you need alignment?**
A tilted face gives a different embedding. Straightening it using the eyes/nose/mouth points makes recognition much more accurate.

**Q: Why tracking? Isn't detection enough?**
Detection doesn't know identity across frames. Tracking lets us say "the *same* face matched 3 times", which makes the decision reliable.

**Q: How do you reduce false alarms?**
Three layers: quality check (ignore bad faces) → threshold (0.363) → multi-frame verification (3 of 5 checks on the same tracked face).

**Q: Why only the latest frame? Aren't you losing frames?**
Yes, on purpose. For live surveillance the freshest frame is most useful; processing old frames would delay alerts.

**Q: How does it scale with many missing persons?**
Embeddings are kept in memory and compared with one matrix multiplication — hundreds of persons are still instant. For millions, a vector database could be added later.

**Q: What if the person turns their face?**
We register 5 poses + mirror images, and allow faces turned up to ~40°. Fully side faces are skipped on purpose (the model is unreliable there); the system waits for a better frame.

**Q: How did you choose 0.363?**
It is the threshold published with the SFace model. Our own tests showed same-person scores around 0.7 and different people near 0.0–0.2, so it gives a clear safety margin.

---

## 8. How it connects with teammates

- **From Member 1:** registered person + photo → our `ReferenceStore.add(person_id, name, photos)` turns it into embeddings.
- **To Member 3:** every confirmed match is sent as a result containing: person ID, name, confidence, time, camera ID, location, scene image, face image.

---

## 9. Limitations & future work (be honest — professors like this)

- Very low light, masks, or heavy face covering reduce accuracy.
- Fully side-on faces are not recognised (by design).
- Thresholds were tested on a small set of images; more real CCTV testing would fine-tune them.
- Future: GPU support for many cameras, a vector database for very large records, WebRTC for even lower streaming delay.

---

## 10. How to demo (2 minutes)

```
venv\Scripts\activate
python us-05\reference_store.py capture MP001 "Your Name"    (follow 5 poses, SPACE each, then Q)
python main.py
```
1. Show your face → box goes **green → orange (verifying) → red "MATCH"**.
2. Ask someone else to stand in front → stays **green** (not matched).
3. Open `data\evidence\` → show the saved scene photo.
4. Run `python us-12\detection_history.py` → show the detection history.
