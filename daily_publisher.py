import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Twin Style: Matching Looks, Double Confidence",
        "K-Fashion Trends You Need to Try",
        "Sisters Share Their Daily Outfit Formula",
        "Aesthetic Moments With Yuna & Aeri",
        "K-Beauty Secrets for a Glowing Look",
        "How We Style the Same Outfit Two Ways",
        "Twin Vibes, Endless Style",
        "Korean Street Style Inspiration",
        "Our Favorite Aesthetic Trends Right Now",
        "Daily Looks That Define Us",
        "Beauty Together: Our Routine",
        "Minimalist K-Style That Works Everywhere",
        "The Confidence of Coordinated Outfits",
        "Sisterhood and Style — What We Love",
        "From Seoul With Love: Fashion Duo",
    ]

    fallback_descriptions = [
        "There's nothing like sharing style with your sister — double the outfits, double the fun, double the confidence. We love matching looks and putting our own spin on the same pieces. Which twin style would you try? Comment your favorite below! 💕 #twins #sisterstyle #koreanfashion #outfitideas #yunaaeri",
        "K-fashion is all about clean lines, soft colors, and effortless layering. From oversized blazers to flowy skirts, the trends are versatile enough for every body. Here's how we make them our own. Save this for your next outfit inspiration! 🍑 #kfashion #koreanstyle #trends #outfitinspo #fashionduo #yunaaeri",
        "The beauty of being a fashion duo is seeing how two people can wear the same thing completely differently. One of us loves minimal, the other loves bold — and both work. Style is personal. Which vibe matches yours? 👯‍♀️ #fashionduo #personalstyle #twins #styleinspo #koreanfashion #yunaaeri",
        "K-beauty is all about healthy, glowing skin. Layered skincare, gentle routines, and sun protection are the foundation of that luminous look. Great skin is the best makeup — start simple and stay consistent. Like if you're on your glow-up journey! ✨ #kbeauty #skincare #glowingskin #beautyroutine #glassskin #yunaaeri",
        "Aesthetic isn't just a look — it's a mood. Soft lighting, curated outfits, and moments that feel like a film still. We chase those little pockets of beauty in everyday life. Drop a 🌸 if you love aesthetic content! #aesthetic #aestheticoutfits #koreanstyle #lifestyle #visualdiary #yunaaeri",
        "One piece, two looks — that's our superpower as sisters. A single blazer becomes office-chic on one of us and street-style on the other. Fashion is about creativity, not rules. Double tap if you love styling hacks! 🧥 #stylinghacks #outfitideas #twinstyle #koreanfashion #versatilefashion #yunaaeri",
        "Trends come and go, but confidence is forever. Wear what makes you feel good, ignore the noise, and own your look. That's the real fashion secret we've learned. Comment one trend you'll never give up! 💅 #confidence #stylewisdom #koreanfashion #selflove #trends #yunaaeri",
        "Every day is a chance to curate your own little aesthetic — your outfit, your energy, your vibe. We document the moments that feel like us. Life is art when you pay attention. Save this for a little inspiration. 🎨 #aesthetic #lifestyle #dailyinspiration #koreanstyle #artofdaily #yunaaeri",
        "Sisterhood means someone who always has your back — and your fashion advice. We push each other to try new styles and cheer each other on. That's the beauty of doing it together. Share this with your sister or your best friend! 💞 #sisterhood #friendship #twinbond #stylepartners #support #yunaaeri",
        "Korean street style inspires us daily — the mix of comfort and polish, the unexpected accessories, the quiet confidence. It's fashion that feels like self-expression rather than costume. Which street look is your favorite? Comment below! 🏙️ #koreansstreetstyle #kfashion #streetfashion #styleinspo #lookbook #yunaaeri",
        "Minimal K-style is our daily uniform — a clean palette, quality basics, and one statement piece. It's simple, chic, and works everywhere from coffee dates to photoshoots. Save this for your minimalist wardrobe guide! 🤍 #minimalstyle #koreanfashion #capsulewardrobe #cleanaesthetic #styleguide #yunaaeri",
        "Beauty is better together — swapping skincare, sharing products, and cheering each other on. These are the little rituals that make sisterhood special. What's your favorite beauty ritual with your sister or friend? Drop it below! 💖 #beautytogether #sisterhood #skincareroutine #kbeauty #selfcare #yunaaeri",
        "We're from Seoul with love, bringing you the fashion and beauty we're obsessed with. From K-trends to daily looks, this is our little corner of the internet. Thanks for being here with us. Double tap to say hi! 👋 #koreancreator #fashionblog #beautyblog #korea #seoul #yunaaeri",
        "Confidence is our favorite accessory — and we love helping each other find it. Style is one way we express who we are and remind ourselves of our worth. Wear your confidence like a crown. Drop a 👑 if you agree! #confidence #selfworth #style #sisterhood #empowerment #yunaaeri",
        "Some days you dress for the mood, some days you dress for the plan — either way, you're showing up. Our daily looks are a reflection of how we feel and what we love. Thanks for joining our fashion journey. What should we style next? Comment your idea! ✨ #dailylook #outfitideas #koreanfashion #fashionjourney #yunaaeri",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "playful and trendy — speak like two stylish Korean sisters having fun",
        "fresh and aesthetic — celebrate clean, soft visuals and daily outfits",
        "sisterly and warm — speak as a close duo who share everything",
        "bold and confident — inspire viewers to own their personal style",
        "girly and cute — make viewers smile with twin energy and k-beauty vibes",
        "aspirational and curated — showcase K-fashion trends and aesthetic moments",
        "cheerful and empowering — celebrate sisterhood, confidence and self-love",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Yuna Aeri'. "
        f"The page is a Korean fashion duo - two sisters sharing fashion, beauty, and lifestyle content. It covers daily outfits, K-fashion trends, and aesthetic moments, with twin vibes, endless style and confidence, inspiring beauty together one post at a time. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if you love twin style! Comment which look is your favorite! Share this with your sister or bestie! Follow Yuna and Aeri for daily K-fashion inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #koreanfashion #kfashion #fashion #beauty #lifestyle #twins #style #outfitideas #kbeauty #aesthetic #trends #sisterstyle #dailylook #yunaaeri. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["koreanfashion", "kfashion", "fashion", "beauty", "lifestyle", "twins", "style", "outfitideas", "kbeauty", "aesthetic", "trends", "sisterstyle", "dailylook", "yunaaeri"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
