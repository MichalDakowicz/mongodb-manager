**MongoDB Manager** to aplikacja stworzona w ramach projektu z baz danych, umożliwiająca zarządzanie kolekcjami w MongoDB.




## 1. Kolekcje bazy danych

Użytkownik może wybrać kolekcję, na której chce wykonać operacje:

- `Pracownicy`
- `Produkty`
- `Klienci`
- `Zamówienia`

![Interfejs aplikacji](image.png)



---

## 2. Wyświetlanie dokumentów

Użytkownik ma możliwość:

- Wybierania pól (np. `imie`, `wynagrodzenie`, `rok_zatrudnienia`)
- Doboru operatorów: `==`, `>`, `<`, itp.
- Określenia typu wartości: `String`, `Liczba`, `Data`
- Dodawania wielu warunków przy użyciu przycisku **Dodaj Warunek (AND)**
- Sortowania wyników (rosnąco/malejąco)
- Ustawienia limitu wyników



![Wybór kolekcji](image-2.png)

Po kliknięciu **Wyszukaj**, wyświetlają się:

- Szczegóły zapytania
- Lista wyników z danymi dokumentów (np. imię, stanowisko, email, ID)
- Możliwość podglądu każdego dokumentu


![alt text](image-11.png)



---

##  3. Aktualizowanie dokumentow

Użytkownik może:

- Wybrać z pól (np. `imie`, `wynagrodzenie`, `rok_zatrudnienia`)
- Doboru operatorów: `==`, `>`, `<`, itp.
- Określenia typu wartości: `String`, `Liczba`, `Data` itp.
- Dodawania wielu warunków przy użyciu przycisku **Dodaj Warunek (AND)**
- Wskazać operację aktualizacji (np.`$set`, `$inc`, `$mul`)
- Wskazać pole które ma uledz zmianie
- Wskazać wartość która zostanie podmieniona za stare dane
- Wskazać nowy typ wartości 
- Wybrać zakres:
  - `updateOne` – aktualizuje pierwszy pasujący dokument
  - `updateMany` – aktualizuje wszystkie pasujące dokumenty
- Zaznaczyć opcję **Upsert**, aby utworzyć dokument, jeśli żaden nie spełnia kryteriów
- Kliknąć **Wykonaj Aktualizację**, aby zastosować zmiany



![Dynamiczne zapytania](image-3.png)  

Po operacji wyświetlane jest podsumowanie:

- Liczba dopasowanych dokumentów
- Liczba zmodyfikowanych dokumentów
- Szczegóły zapytania i wykonanych zmian

![Wyniki zapytania](image-13.png)



---

## 🗑️ 4.Usuwanie dokumentów

Użytkownik może:

- Wybrać z pól (np. `imie`, `wynagrodzenie`, `rok_zatrudnienia`)
- Doboru operatorów: `==`, `>`, `<`, itp.
- Określenia typu wartości: `String`, `Liczba`, `Data` itp.
- Dodawania wielu warunków przy użyciu przycisku **Dodaj Warunek (AND)**
- Wybrać zakres:
  - `updateOne` – aktualizuje pierwszy pasujący dokument
  - `updateMany` – aktualizuje wszystkie pasujące dokumenty
- Kliknąć **Wykonaj Usuwanie**, aby zastosować zmiany


![Aktualizacja dokumentów](image-15.png)  

Przed operacją wyświetlane jest ostrzeżenie o jej nieodwracalności.

![Podsumowanie aktualizacji](image-16.png)

Po wykonaniu:

- Liczba usuniętych dokumentów
- Szczegóły operacji

![Podsumowanie aktualizacji](image-17.png)


---

##  5. Edycja dokumentu po ID

Użytkownik może:

- Wprowadzić **ObjectId** dokumentu
- Wskazać pole do aktualizacji
- Wskazać nową wartość
- Wskazać typ nowej wartości
- Kliknąć **Zapisz Zmiany**, aby zaktualizować dokument



![Aktualizacja dokumentów](image-5.png)  

- Program wyswietla powiadomienie o pozytywnym wykonaniu polecenia

![alt text](image-25.png)

---

## 6. Czyszczenie całej kolekcji

Użytkownik może:

- Trwale usunąć **wszystkie dokumenty** z kolekcji( Obowiązkowo trzeba zaznaczyć pole **Tak, rozumiem i chcę usunąć wszystkie dokumenty**)
- Kliknąć **Usuń Wszystko!**, aby potwierdzić



![Czyszczenie kolekcji](image-9.png)

Użytkownik potwierdza wykonanie operacji:

![alt text](image-23.png)

Aplikacja wyswitla komunikat o usunięciu dokumentów z kolekkcji:

![alt text](image-24.png)

---

## 7. Wyświetlanie zawartości poszczególnych kolekcji z możliwością ograniczenia liczby wyświetlanych dokumentów

![alt text](<Zrzut ekranu 2025-06-02 182212-1.png>)

## 8. Predefiniowane operacje

Aplikacja oferuje zestaw predefiniowanych operacji, podzielonych na trzy kategorie:

- **Wszystkie Wyszukiwania**  
  Szybki dostęp do najczęściej używanych zapytań:
  - Pracownicy na stanowisku 'Programista'
  - Pracownicy z wynagrodzeniem > X
  - Pracownicy zatrudnieni w 2023
  - Nieaktywni pracownicy

- **Agregacje**  
  Gotowe raporty i statystyki:
  - Średnie wynagrodzenie na stanowisko
  - Liczba pracowników na miasto
  - Popularność umiejętności
  - Średnie wynagrodzenie wg statusu aktywności

- **Aktualizacje**  
  Szybkie operacje modyfikujące dane:
  - Zwiększ wynagrodzenie Analitykom o 10%
  - Dezaktywuj losowego pracownika

![alt text](image-26.png)

Każda operacja może być uruchomiona jednym kliknięciem, a wyniki sa przedstawine w taki sam sposób jak przy operacjach dynamicznych.

![alt text](image-27.png)

## 9. Przycisk - Dodaj losowe

Użytkownik może dodać 10 dokumentów z losowymi danymi.

![alt text](image-28.png)

Po wykonaniu wyświetla się komunikat o wykonaniu zadania:

![alt text](image-29.png)


## 10. Zadania

### I. Dodaj po 10 dokumentów do kolekcji. | II. Wykonaj wyświetlanie zawartości poszczególnych kolekcji z możliwością ograniczenia liczby wyświetlanych dokumentów.

Użytkownik używa przycisku dodaj losowe w prawym górnym rogu strony, który dodaje 10 dokumentów wypełnionych losowymi danymi.
Czynność zostaje powtórzona we wszystkich czterech kolekcjach. 

![alt text](image-30.png)

Po naciśnięciu przycisku program wyświetla komunikat o dodaniu 10 dokumentów do kolekcji pracownicy.

![alt text](image-31.png)

Po naciśnięciu przycisku wyświetl dokumenty program przenosi użytkownika do strony, która wyświetla zawartości poszczególnych kolekcji z możliwością ograniczenia liczby
wyświetlanych dokumentów.

![alt text](image-32.png)


III. Wykonaj 6 przykładowych poleceń wyszukujących dokumenty spełniające narzucone kryteria

Polecenie 1:

![alt text](image-33.png)

![alt text](image-34.png)

Polecenie 2:

![alt text](image-35.png)

![alt text](image-36.png)

Polecenie 3:

![alt text](image-37.png)

![alt text](image-38.png)

Polecenie 4:

![alt text](image-39.png)

Jeżeli nie ma wyników wyszukiwania wyświetla się komunikat.

![alt text](image-40.png)

Polecenie 5:

![alt text](image-41.png)

![alt text](image-42.png)

Polecenie 6:

![alt text](image-43.png)

![alt text](image-44.png)

IV. Wykonaj 6 przykładowych poleceń aktualizujących dokumenty spełniające narzucone kryteria

Polecenie 1:

![alt text](image-45.png)

![alt text](image-46.png)

Polecenie 2:

![alt text](image-47.png)

![alt text](image-48.png)

Polecenie 3:

![alt text](image-49.png)

![alt text](image-50.png)

Polecenie 4:

![alt text](image-51.png)

![alt text](image-52.png)

Polecenie 5:

![alt text](image-53.png)

![alt text](image-54.png)

Polecenie 6:

![alt text](image-55.png)

![alt text](image-56.png)

V. Wykonaj 3 przykładowe polecenia wyszukujące dokumenty spełniające narzucone kryteria.

Polecenie 1:

![alt text](image-57.png)

Polecenie nie odnalazło dokumentów ponieważ wcześniej został on zupdatowany.

![alt text](image-58.png)

Polecenie 2:

![alt text](image-60.png)

Polecenie wyszukało użytkownika z imieniem Krystian czyli zgodnie z wcześniejszym updatem.

![alt text](image-61.png)

Polecenie 3:

![alt text](image-62.png)

Polecenie nie odnalazło dokumentów ponieważ we wcześniejszym updacie liczby mniejsze niż 9000 zostały pomnożone przez 7.

![alt text](image-63.png)

