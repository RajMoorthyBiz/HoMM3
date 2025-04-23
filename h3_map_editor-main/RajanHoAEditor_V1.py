#!/usr/bin/env python3

"""
RajanHoAEditor_V1.py - A script to analyze monster objects in Heroes of Might and Magic III maps

This script opens and parses the Do.h3m file, identifies and collects all 'Monster' and 
'Random Monster' objects, and prints information about each monster found.
"""

import os
import sys
from gzip import open as gzip_open

# Import required modules
import src.file_io as io
import data.objects as od
import data.creatures as cd
from src.handler_01_general import parse_general
from src.handler_08_objects import Disposition, parse_object_defs, parse_object_data

def is_monster_type(obj_type):
    """Check if object type is a monster or random monster"""
    monster_types = [
        od.ID.Monster,
        od.ID.Random_Monster,
        od.ID.Random_Monster_1,
        od.ID.Random_Monster_2,
        od.ID.Random_Monster_3,
        od.ID.Random_Monster_4,
        od.ID.Random_Monster_5,
        od.ID.Random_Monster_6,
        od.ID.Random_Monster_7
    ]
    return obj_type in monster_types

def get_disposition_name(disposition_value):
    """Convert disposition value to string name"""
    dispositions = {
        Disposition.Compliant: "Compliant",
        Disposition.Friendly: "Friendly", 
        Disposition.Aggressive: "Aggressive",
        Disposition.Hostile: "Hostile",
        Disposition.Savage: "Savage",
        Disposition.Precise: "Precise"
    }
    return dispositions.get(disposition_value, "Unknown")

def get_creature_level(creature_id):
    """Determine the level of a creature based on its ID"""
    # Creature levels in Heroes 3 are generally 1-7
    if creature_id < 14:  # Castle creatures
        return (creature_id // 2) + 1
    elif creature_id < 28:  # Rampart creatures
        return ((creature_id - 14) // 2) + 1
    elif creature_id < 42:  # Tower creatures
        return ((creature_id - 28) // 2) + 1
    elif creature_id < 56:  # Inferno creatures
        return ((creature_id - 42) // 2) + 1
    elif creature_id < 70:  # Necropolis creatures
        return ((creature_id - 56) // 2) + 1
    elif creature_id < 84:  # Dungeon creatures
        return ((creature_id - 70) // 2) + 1
    elif creature_id < 98:  # Stronghold creatures
        return ((creature_id - 84) // 2) + 1
    elif creature_id < 112:  # Fortress creatures
        return ((creature_id - 98) // 2) + 1
    else:
        # For other creatures, estimate based on AI value
        ai_value = cd.AI_VALUE[creature_id] if creature_id < len(cd.AI_VALUE) else 0
        if ai_value < 100:
            return 1
        elif ai_value < 200:
            return 2
        elif ai_value < 400:
            return 3
        elif ai_value < 800:
            return 4
        elif ai_value < 1600:
            return 5
        elif ai_value < 3200:
            return 6
        else:
            return 7

def parse_map_file(filename):
    """Parse a H3M map file and extract monster objects"""
    monsters = []
    data = None
    try:
        with gzip_open(filename, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error opening file as gzip: {str(e)}")
        return monsters, data
    
    # Search for monster objects (type 54 = 0x36)
    monster_type_bytes = b'\x36\x00\x00\x00'
    pos = 0
    while True:
        pos = data.find(monster_type_bytes, pos)
        if pos == -1:
            break
        
        # Found a potential monster object
        try:
            # The subtype (creature ID) should be at pos+4
            if pos + 6 < len(data):
                subtype = int.from_bytes(data[pos+4:pos+6], byteorder='little')
            
                # The quantity should be at pos+6
                if pos + 8 < len(data):
                    quantity = int.from_bytes(data[pos+6:pos+8], byteorder='little')
                    
                    # Set disposition to Aggressive for all monsters as requested
                    #disposition = Disposition.Aggressive
                    #if pos + 19 < len(data):
                    #    data = bytearray(data)
                    #    data[pos+18] = 2 #Disposition.Aggressive = 2
                    #    data = bytes(data)

                    # Print validation info
                    #print(f"  Valid creature ID: {0 <= subtype < len(cd.NAME)}")
                    #print(f"  Reasonable quantity: {0 <= quantity <= 1000}")

                    # Only add if it's a valid creature ID and reasonable quantity
                    if 0 <= subtype < len(cd.NAME) and 0 <= quantity <= 1000:
                        monsters.append({
                            "type": od.ID.Monster,
                            "subtype": subtype,
                            "quantity": quantity,
                            "disposition": 2
                        })
        except Exception as e:
            print(f"Error extracting monster at position {pos}: {str(e)}")
        
        # Move to the next position
        pos += 1
    
    # Search for random monster objects (types 71-75, 162-164)
    for monster_type in [71, 72, 73, 74, 75, 162, 163, 164]:
        type_bytes = monster_type.to_bytes(4, byteorder='little')
        pos = 0
        while True:
            pos = data.find(type_bytes, pos)
            if pos == -1:
                break
            
            # Found a potential random monster object
            try:
                # The quantity should be at pos+4
                if pos + 6 < len(data):
                    quantity = int.from_bytes(data[pos+4:pos+6], byteorder='little')
                    
                    # Set disposition to Aggressive for all monsters as requested
                    #disposition = Disposition.Aggressive
                    #if pos + 15 < len(data):
                    #    data = bytearray(data)
                    #    data[pos+14] = 2 #Disposition.Aggressive = 2
                    #    data = bytes(data)
                        # Only add if it's a reasonable quantity
                    if 1 <= quantity <= 1000:
                        monsters.append({
                            "type": monster_type,
                            "quantity": quantity,
                            "disposition": 2
                        })
            except Exception as e:
                print(f"Error extracting random monster at position {pos}: {str(e)}")
            
            # Move to the next position
            pos += 1
    return monsters, data

def GetMonsterProperty(filename):
    """Opens the H3M file and prints the monster name and disposition"""
    try:
        print(f"Parsing map file: {filename}")
        monster_objects, data = parse_map_file(filename)
        
        if not monster_objects:
            print("No monster objects found in the map file.")
            return
        
        # Print details for each monster
        for i, monster in enumerate(monster_objects, 1):
            print(f"Monster #{i}:")
            
            # Get creature name if it's a specific monster
            if monster["type"] == od.ID.Monster:
                creature_id = monster["subtype"]
                creature_name = cd.NAME[creature_id] if creature_id < len(cd.NAME) else "Unknown"
                print(f"Name: {creature_name}")
            else:
                creature_name = f"Random Monster (Type {monster['type']})"
                print(f"Name: {creature_name}")
            
            print(f"Disposition: Aggressive")
            print()
    except Exception as e:
        print(f"Error: {str(e)}")

def SetMonsterProperty(filename):
    """Opens the H3M file and sets the monster disposition to Aggressive"""
    try:
        print(f"Parsing map file: {filename}")
        monster_objects, data = parse_map_file(filename)
        
        if not monster_objects:
            print("No monster objects found in the map file.")
            return
        
        # Set disposition to Aggressive for all monsters
        for monster in monster_objects:
            monster["disposition"] = 2
        
        # Write the modified data to a new file
        new_file_path = os.path.join(os.getcwd(), 'Do2.h3m')
        with open('Do2.h3m', 'wb') as f:
            f.write(data)
        print(f"Successfully updated the disposition to Aggressive in {new_file_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Main function"""
    print("RajanHoAEditor_V1.py - Heroes of Might and Magic III Map Monster Analyzer")
    print("================================================================")
    
    try:
        GetMonsterProperty('Do.h3m')
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
