//! Días hábiles Colombia (fin de semana + festivos CO) alineados a `holidays.CO` vía JSON estático.

use std::collections::HashSet;
use std::sync::LazyLock;

use chrono::{Datelike, Duration, NaiveDate, Weekday};

static CO_HOLIDAYS: LazyLock<HashSet<NaiveDate>> = LazyLock::new(|| {
    let raw = include_str!("../data/co_holidays.json");
    let v: Vec<String> = serde_json::from_str(raw).expect("co_holidays.json inválido");
    v.into_iter()
        .map(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").expect("fecha festivo"))
        .collect()
});

fn es_dia_habil(d: NaiveDate) -> bool {
    if matches!(d.weekday(), Weekday::Sat | Weekday::Sun) {
        return false;
    }
    !CO_HOLIDAYS.contains(&d)
}

/// Igual que `prioritization.calendario_colombia.cuenta_dias_habiles_entre`.
pub fn cuenta_dias_habiles_entre(inicio: NaiveDate, fin: NaiveDate) -> i32 {
    if fin < inicio {
        return 0;
    }
    let mut n = 0i32;
    let mut d = inicio;
    while d < fin {
        d += Duration::days(1);
        if es_dia_habil(d) {
            n += 1;
        }
    }
    n
}

/// Igual que `prioritization.calendario_colombia.dias_habiles_restantes_hasta`.
pub fn dias_habiles_restantes_hasta(hoy: NaiveDate, limite: NaiveDate) -> i32 {
    if limite < hoy {
        return -cuenta_dias_habiles_entre(limite, hoy);
    }
    cuenta_dias_habiles_entre(hoy, limite)
}
