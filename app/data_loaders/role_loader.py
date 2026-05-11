from app.core.db_conn import SessionLocal
from app.models import Role

def seed_roles_final():
    db = SessionLocal()
    
    # 6 зон и соответствующие им роли из статьи
    data = {
        "Goalkeeper": [
            "Line Keeper", "Sweeper Keeper", "Ball Playing Keeper"
        ],
        "Center Back": [
            "Sweeper", "Ball Playing Defender", "Stopper"
        ],
        "Full Back": [
            "Full Back", "Wing Back", "Inverted Wing Back"
        ],
        "Central Midfielder": [
            "Ball Winning Midfielder", "Deep Lying Playmaker", "Holding Midfielder",
            "Box To Box Midfielder", "Advanced Playmaker"
        ],
        "Wide Midfielder": [
            "Wide Playmaker", "Winger"
        ],
        "Forward": [
            "Inside Forward", "Second Striker", "Mobile Striker", "Target Man", "Poacher"
        ]
    }

    print(">>> Populating roles with 6-zone English structure...")
    
    added = 0
    for zone_name, roles in data.items():
        for r_name in roles:
            # Проверка наличие пары
            exists = db.query(Role).filter(
                Role.role_name == r_name, 
                Role.zone == zone_name
            ).first()
            
            if not exists:
                new_role = Role(
                    role_name=r_name,
                    zone=zone_name,
                    role_description=f"Professional football role: {r_name} ({zone_name})"
                )
                db.add(new_role)
                added += 1
    
    try:
        db.commit()
        print(f"DONE: Added {added} unique roles to the database.")
    except Exception as e:
        db.rollback()
        print(f"CRITICAL ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_roles_final()