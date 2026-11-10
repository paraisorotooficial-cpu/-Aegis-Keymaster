"""
Script de prueba para verificar que todos los módulos funcionen correctamente
"""

def test_sound_engine():
    print("Testing Sound Engine...")
    from sound_engine import SoundEngine
    audio = SoundEngine()
    print(f"  - Audio enabled: {audio.enabled}")
    print("  ✓ Sound Engine OK")

def test_tips_system():
    print("\nTesting Tips System...")
    from tips_system import TipsSystem
    tips = TipsSystem()
    
    # Test random tip
    tip = tips.get_tip()
    print(f"  - Random tip: {tip[:60]}...")
    
    # Test concept-specific tip
    tip = tips.get_tip_for_concept("variables")
    print(f"  - Variables tip: {tip[:60]}...")
    
    # Test topics
    topics = tips.get_all_topics()
    print(f"  - Total topics: {len(topics)}")
    print("  ✓ Tips System OK")

def test_content_generator():
    print("\nTesting Content Generator...")
    from content_generator import ContentGenerator
    content = ContentGenerator()
    
    # Test regular challenge
    challenge = content.get_challenge(5)
    print(f"  - Challenge text: {challenge.text}")
    print(f"  - Challenge concept: {challenge.concept}")
    
    # Test code builder exercise
    exercise = content.get_code_builder_exercise(difficulty=3)
    print(f"  - Code exercise title: {exercise['title']}")
    print(f"  - Code exercise lines: {len(exercise['code'].split(chr(10)))}")
    
    # Test categories
    categories = content.get_code_builder_categories()
    print(f"  - Code categories: {len(categories)}")
    print("  ✓ Content Generator OK")

def test_achievements():
    print("\nTesting Achievements...")
    from achievements import AchievementManager
    ach_mgr = AchievementManager()
    
    total = ach_mgr.get_total_count()
    unlocked = ach_mgr.get_unlocked_count()
    print(f"  - Total achievements: {total}")
    print(f"  - Unlocked: {unlocked}")
    print("  ✓ Achievements OK")

def test_profile():
    print("\nTesting Profile Manager...")
    from profile_manager import PlayerProfile
    profile = PlayerProfile()
    
    print(f"  - Level: {profile.level}")
    print(f"  - Rank: {profile.rank}")
    print(f"  - XP: {profile.xp}/{profile.xp_for_next_level}")
    print(f"  - Accuracy: {profile.accuracy:.1f}%")
    print("  ✓ Profile Manager OK")

if __name__ == "__main__":
    print("=" * 60)
    print("KeyMaster Pro - Module Testing")
    print("=" * 60)
    
    try:
        test_sound_engine()
        test_tips_system()
        test_content_generator()
        test_achievements()
        test_profile()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nLa aplicación está lista para ejecutarse.")
        print("Ejecuta: python keymaster.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()