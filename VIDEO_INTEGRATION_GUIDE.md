# 🎥 How to Add Video to Homepage

## Option 1: Animated Hero Section (Immediate Solution)

I've created `ANIMATED_HERO_SECTION.html` with a video-like animated introduction that you can use **right now**!

### Features:
- ✅ Floating particle animations
- ✅ Smooth fade-in effects
- ✅ Animated counters
- ✅ Glassmorphism design
- ✅ No video file needed
- ✅ Fast loading
- ✅ Works on all devices

### How to Use:
1. Open `ANIMATED_HERO_SECTION.html`
2. Copy all the code
3. Replace the hero section in `templates/index.html`
4. Refresh your homepage
5. Enjoy the animated introduction!

---

## Option 2: Actual Video (Once You Create It)

### Step 1: Create Your Video

Use the script from `VIDEO_SCRIPT_STORYBOARD.md` with these tools:

**Quick & Easy** (30 minutes):
- **Canva** - canva.com
  - Search "App Promo Video"
  - Use template
  - Customize with your text
  - Download

**Professional** (2-3 hours):
- **Synthesia** - synthesia.io
- **Pictory** - pictory.ai
- **Runway ML** - runwayml.com

### Step 2: Optimize Your Video

```bash
# Compress video for web (using FFmpeg)
ffmpeg -i input.mp4 -vcodec h264 -acodec aac -b:v 1M -b:a 128k output.mp4

# Create thumbnail
ffmpeg -i input.mp4 -ss 00:00:01 -vframes 1 thumbnail.jpg
```

**Recommended Settings**:
- Format: MP4 (H.264)
- Resolution: 1920x1080
- Size: < 5MB
- Duration: 30-45 seconds

### Step 3: Add Video to Your Project

**Upload video to your project**:
```
AI_Eval-main/
  static/
    videos/
      intro.mp4        ← Your video here
      intro-thumb.jpg  ← Thumbnail
```

### Step 4: Add Video HTML to Homepage

Replace the hero section in `templates/index.html` with this:

```html
<section class="hero-video-container">
    <div class="video-wrapper">
        <!-- Background Video -->
        <video 
            id="heroVideo" 
            class="hero-video" 
            autoplay 
            muted 
            loop 
            playsinline
            poster="{{ url_for('static', filename='videos/intro-thumb.jpg') }}"
        >
            <source src="{{ url_for('static', filename='videos/intro.mp4') }}" type="video/mp4">
            Your browser does not support the video tag.
        </video>

        <!-- Overlay Content -->
        <div class="video-overlay">
            <div class="video-content">
                <h1 class="video-title">AI-Powered Candidate Evaluation</h1>
                <p class="video-subtitle">The Future of Technical Interviews</p>
                <a href="{{ url_for('register') }}" class="video-cta">
                    <i class="fas fa-rocket"></i> Get Started Free
                </a>
            </div>
        </div>

        <!-- Video Controls (Optional) -->
        <div class="video-controls">
            <button id="playPauseBtn" class="control-btn">
                <i class="fas fa-pause"></i>
            </button>
            <button id="muteBtn" class="control-btn">
                <i class="fas fa-volume-up"></i>
            </button>
        </div>
    </div>
</section>

<style>
    .hero-video-container {
        position: relative;
        width: 100%;
        height: 100vh;
        min-height: 600px;
        overflow: hidden;
    }

    .video-wrapper {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .hero-video {
        position: absolute;
        top: 50%;
        left: 50%;
        min-width: 100%;
        min-height: 100%;
        width: auto;
        height: auto;
        transform: translate(-50%, -50%);
        object-fit: cover;
        z-index: 1;
    }

    .video-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2;
    }

    .video-content {
        text-align: center;
        color: white;
        max-width: 800px;
        padding: 2rem;
        animation: fadeInUp 1s ease-out;
    }

    .video-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    .video-subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    }

    .video-cta {
        display: inline-block;
        padding: 1.25rem 3rem;
        font-size: 1.25rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50px;
        text-decoration: none;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    .video-cta:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
    }

    .video-controls {
        position: absolute;
        bottom: 2rem;
        right: 2rem;
        display: flex;
        gap: 1rem;
        z-index: 3;
    }

    .control-btn {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.3);
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .control-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: scale(1.1);
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 768px) {
        .video-title {
            font-size: 2.5rem;
        }

        .video-subtitle {
            font-size: 1.2rem;
        }

        .video-cta {
            padding: 1rem 2rem;
            font-size: 1.1rem;
        }
    }
</style>

<script>
    // Video controls
    const video = document.getElementById('heroVideo');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const muteBtn = document.getElementById('muteBtn');

    // Play/Pause toggle
    playPauseBtn.addEventListener('click', () => {
        if (video.paused) {
            video.play();
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            video.pause();
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    });

    // Mute/Unmute toggle
    muteBtn.addEventListener('click', () => {
        video.muted = !video.muted;
        muteBtn.innerHTML = video.muted 
            ? '<i class="fas fa-volume-mute"></i>' 
            : '<i class="fas fa-volume-up"></i>';
    });

    // Auto-play with sound after user interaction
    document.addEventListener('click', () => {
        if (video.paused) {
            video.play();
        }
    }, { once: true });
</script>
```

---

## Option 3: YouTube Embed (Easiest)

If you upload your video to YouTube:

```html
<section class="hero-youtube">
    <div class="youtube-wrapper">
        <iframe 
            width="100%" 
            height="600" 
            src="https://www.youtube.com/embed/YOUR_VIDEO_ID?autoplay=1&mute=1&loop=1&playlist=YOUR_VIDEO_ID"
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen
        ></iframe>
    </div>
    
    <div class="youtube-overlay">
        <h1>AI-Powered Candidate Evaluation</h1>
        <a href="{{ url_for('register') }}" class="btn btn-primary">Get Started</a>
    </div>
</section>

<style>
    .hero-youtube {
        position: relative;
        width: 100%;
        height: 600px;
        overflow: hidden;
    }

    .youtube-wrapper {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 100vw;
        height: 100vh;
        transform: translate(-50%, -50%);
        pointer-events: none;
    }

    .youtube-wrapper iframe {
        width: 100vw;
        height: 100vh;
        pointer-events: none;
    }

    .youtube-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.3);
        color: white;
        z-index: 2;
    }
</style>
```

---

## Performance Optimization

### 1. Lazy Loading

```html
<video 
    id="heroVideo" 
    class="hero-video" 
    autoplay 
    muted 
    loop 
    playsinline
    preload="metadata"  <!-- Only load metadata initially -->
    poster="{{ url_for('static', filename='videos/intro-thumb.jpg') }}"
>
```

### 2. Responsive Videos

```html
<!-- Serve different videos for mobile -->
<video id="heroVideo" class="hero-video" autoplay muted loop playsinline>
    <source 
        src="{{ url_for('static', filename='videos/intro-mobile.mp4') }}" 
        type="video/mp4" 
        media="(max-width: 768px)"
    >
    <source 
        src="{{ url_for('static', filename='videos/intro.mp4') }}" 
        type="video/mp4"
    >
</video>
```

### 3. Fallback Image

```html
<video 
    id="heroVideo" 
    class="hero-video" 
    autoplay 
    muted 
    loop 
    playsinline
    poster="{{ url_for('static', filename='videos/intro-thumb.jpg') }}"
    onerror="this.style.display='none'; document.getElementById('fallbackImage').style.display='block';"
>
    <source src="{{ url_for('static', filename='videos/intro.mp4') }}" type="video/mp4">
</video>

<img 
    id="fallbackImage" 
    src="{{ url_for('static', filename='videos/intro-thumb.jpg') }}" 
    style="display: none; width: 100%; height: 100%; object-fit: cover;"
    alt="Hero Image"
>
```

---

## Best Practices

### ✅ DO:
- Keep video under 5MB
- Use H.264 codec
- Include poster image
- Mute autoplay videos
- Provide controls
- Test on mobile
- Compress properly

### ❌ DON'T:
- Use videos over 10MB
- Autoplay with sound (annoying!)
- Forget mobile optimization
- Skip fallback image
- Use unsupported formats
- Ignore accessibility

---

## Accessibility

```html
<video 
    id="heroVideo" 
    class="hero-video" 
    autoplay 
    muted 
    loop 
    playsinline
    aria-label="Introduction video showing AI-powered evaluation features"
>
    <source src="{{ url_for('static', filename='videos/intro.mp4') }}" type="video/mp4">
    <track 
        kind="captions" 
        src="{{ url_for('static', filename='videos/captions.vtt') }}" 
        srclang="en" 
        label="English"
    >
    Your browser does not support the video tag.
</video>
```

---

## Testing Checklist

- [ ] Video loads on Chrome
- [ ] Video loads on Firefox
- [ ] Video loads on Safari
- [ ] Video loads on mobile
- [ ] Autoplay works
- [ ] Mute works
- [ ] Loop works
- [ ] Controls work
- [ ] Poster image shows
- [ ] Fallback works
- [ ] Performance is good (< 3s load)
- [ ] No layout shift

---

## Quick Start

**Right Now** (0 minutes):
1. Use `ANIMATED_HERO_SECTION.html`
2. Copy to `templates/index.html`
3. Done!

**With Video** (30 minutes):
1. Create video with Canva
2. Upload to `static/videos/`
3. Use HTML code above
4. Test and deploy

**Professional** (2-3 hours):
1. Use Synthesia/Pictory
2. Create professional video
3. Optimize and compress
4. Upload and integrate

---

## Need Help?

If you need assistance:
1. Creating the video → Use Canva (easiest)
2. Compressing video → Use online tools like cloudconvert.com
3. Hosting video → Use your server or YouTube
4. Implementing code → Copy-paste from above

**The animated hero section is ready to use immediately while you create your video!**
