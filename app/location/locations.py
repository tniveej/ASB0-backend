from __future__ import annotations

from typing import Dict, List, Optional, Tuple


MALAYSIA_DISTRICTS: Dict[str, List[str]] = {
    # Peninsular
    "Johor": [
        "Batu Pahat", "Johor Bahru", "Kluang", "Kota Tinggi", "Kulai", "Mersing",
        "Muar", "Pontian", "Segamat", "Tangkak",
    ],
    "Kedah": [
        "Baling", "Bandar Baharu", "Kota Setar", "Kuala Muda", "Kubang Pasu",
        "Kulim", "Langkawi", "Padang Terap", "Pendang", "Pokok Sena", "Sik", "Yan",
    ],
    "Kelantan": [
        "Bachok", "Gua Musang", "Jeli", "Kota Bharu", "Kuala Krai", "Machang",
        "Pasir Mas", "Pasir Puteh", "Tanah Merah", "Tumpat",
    ],
    "Melaka": ["Alor Gajah", "Jasin", "Melaka Tengah"],
    "Negeri Sembilan": [
        "Jelebu", "Jempol", "Kuala Pilah", "Port Dickson", "Rembau", "Seremban", "Tampin",
    ],
    "Pahang": [
        "Bentong", "Bera", "Cameron Highlands", "Jerantut", "Kuantan", "Lipis",
        "Maran", "Pekan", "Raub", "Rompin", "Temerloh",
    ],
    "Perak": [
        "Bagan Datuk", "Batang Padang", "Hilir Perak", "Hulu Perak", "Kampar",
        "Kerian", "Kinta", "Kuala Kangsar", "Larut Matang dan Selama", "Manjung",
        "Muallim", "Perak Tengah",
    ],
    "Perlis": ["Kangar", "Arau", "Padang Besar"],
    "Pulau Pinang": [
        "Timur Laut", "Barat Daya", "Seberang Perai Utara", "Seberang Perai Tengah",
        "Seberang Perai Selatan",
    ],
    "Penang": [
        "Timur Laut", "Barat Daya", "Seberang Perai Utara", "Seberang Perai Tengah",
        "Seberang Perai Selatan",
    ],
    "Selangor": [
        "Gombak", "Hulu Langat", "Hulu Selangor", "Klang", "Kuala Langat",
        "Kuala Selangor", "Petaling", "Sabak Bernam", "Sepang",
    ],
    "Terengganu": [
        "Besut", "Dungun", "Hulu Terengganu", "Kemaman", "Kuala Terengganu",
        "Marang", "Setiu",
    ],
    # Sabah & Sarawak
    "Sabah": [
        "Beaufort", "Beluran", "Keningau", "Kota Belud", "Kota Kinabalu", "Kota Marudu",
        "Kuala Penyu", "Kudat", "Kunak", "Lahad Datu", "Nabawan", "Papar", "Penampang",
        "Pitas", "Ranau", "Sandakan", "Semporna", "Sipitang", "Tambunan", "Tawau",
        "Telupid", "Tenom", "Tongod", "Tuaran", "Putatan",
    ],
    "Sarawak": [
        "Betong", "Bintulu", "Kapit", "Kuching", "Limbang", "Miri", "Mukah",
        "Samarahan", "Sarikei", "Serian", "Sibu", "Sri Aman",
    ],
    # Federal Territories
    "Kuala Lumpur": ["Kuala Lumpur"],
    "Putrajaya": ["Putrajaya"],
    "Labuan": ["Labuan"],
}


def normalize_location(state: Optional[str], district: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not state and not district:
        return None, None

    # Normalize state by case-insensitive match
    normalized_state = None
    for s in MALAYSIA_DISTRICTS.keys():
        if state and s.lower() == state.lower():
            normalized_state = s
            break
    # Allow Penang/Pulau Pinang equivalence
    if not normalized_state and state:
        if state.lower() == "penang":
            normalized_state = "Pulau Pinang"
        elif state.lower() == "pulau pinang":
            normalized_state = "Pulau Pinang"

    normalized_district = None
    if normalized_state and district:
        for d in MALAYSIA_DISTRICTS[normalized_state]:
            if d.lower() == district.lower():
                normalized_district = d
                break

    # If only district known, try to infer state by unique district occurrence
    if not normalized_state and district:
        candidates = [
            s for s, ds in MALAYSIA_DISTRICTS.items() if any(d.lower() == district.lower() for d in ds)
        ]
        if len(candidates) == 1:
            normalized_state = candidates[0]
            for d in MALAYSIA_DISTRICTS[normalized_state]:
                if d.lower() == district.lower():
                    normalized_district = d
                    break

    return normalized_state, normalized_district


