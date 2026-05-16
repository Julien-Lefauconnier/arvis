Oui.
On va faire ça méthodiquement et avec des greps “signal only”.

D’abord nettoyage rapide avant audit :

```bash
find . -type d \( -name "__pycache__" -o -name ".mypy_cache" -o -name ".pytest_cache" -o -name ".ruff_cache" \) -exec rm -rf {} + 2>/dev/null

find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
```

Ensuite, je veux les greps suivants, un par un, avec sortie complète.

---

## 1. Exceptions sauvages

Très important.

```bash
grep -RIn \
  -E "raise (RuntimeError|ValueError|Exception|AssertionError|NotImplementedError)\(" \
  arvis tests
```

---

## 2. Catch globaux dangereux

```bash
grep -RIn \
  -E "except Exception|except BaseException" \
  arvis tests
```

---

## 3. Stockage manuel d’erreurs

On veut détecter les bypass du ErrorManager.

```bash
grep -RIn \
  -E "ctx\.errors|error_state\.errors|extra\[\"errors\"\]|extra\['errors'\]" \
  arvis tests
```

---

## 4. RuntimeError résiduels directs

Même hors raise.

```bash
grep -RIn "RuntimeError" arvis tests
```

---

## 5. TODO/FIXME liés aux erreurs

Souvent révélateurs de dettes structurelles.

```bash
grep -RIn \
  -E "TODO|FIXME|HACK|XXX" \
  arvis/errors arvis/kernel arvis/runtime arvis/adapters
```

---

## 6. Utilisation réelle du ErrorManager

On veut mesurer l’adoption.

```bash
grep -RIn "ErrorManager\." arvis tests
```

---

## 7. Normalisation d’erreurs

Très important pour voir les chemins divergents.

```bash
grep -RIn "normalize_error" arvis tests
```

---

## 8. Usage des boundaries

Pour voir la couverture actuelle.

```bash
grep -RIn "capture_.*failure" arvis tests
```

---

## 9. Erreurs silencieuses

Très critique.

```bash
grep -RIn \
  -E "pass[[:space:]]*$|return None[[:space:]]*$" \
  arvis
```

Je veux surtout voir :

* dans les `except`
* dans les runtime services
* dans les stages
* dans les adapters

---

## 10. Logging direct non orchestré

Pour préparer la future télémétrie propre.

```bash
grep -RIn \
  -E "logger\.(error|exception|warning|critical)" \
  arvis
```

---

## 11. Assertions runtime

Les assertions dans un kernel/runtime sont souvent mauvaises hors tests.

```bash
grep -RIn "assert " arvis
```

---

## 12. Vérification des domains explicites

On veut voir la distribution réelle.

```bash
grep -RIn "domain *= *ErrorDomain" arvis/errors arvis
```

---

## 13. Vérification des policies explicites

```bash
grep -RIn "policy *= *ErrorPolicy" arvis/errors arvis
```

---

## 14. Vérification degraded/retryable

```bash
grep -RIn \
  -E "retryable *=|degraded *=" \
  arvis/errors arvis
```

---

## 15. Vérification replay safety

```bash
grep -RIn "replay_safe" arvis/errors arvis
```

---

Le plus critique dans l’immédiat :

1. exceptions sauvages
2. except Exception
3. stockage manuel
4. silent catches

C’est là que tu vas découvrir si `errors/` est vraiment devenu canonique… ou juste “bien structuré localement”.
