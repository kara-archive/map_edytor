### Zależności
PyQt5 open-cv i oczywiście python
w wersji "light" tylko PyQt5
# Edytor mapkowych
Zrobiony z myślą o systemie z japońskiej, ale można też łatwo dostosować pod inne systemy.
![edytor](https://github.com/user-attachments/assets/9891c921-a229-483b-bd03-09d6c4f4d704)

### Główne ficzery:
  **Tabelka**:
  
  łatwo generuj tabelkę po prostu dodając nazwę państwa i kolor. Program automatycznie policzy i przydzieli prowincje i ikony na mapce.
  
  **Tryb bitew**
  
  odpalany w konsoli automatycznie losuje "kostką" za każdą jednostkę i porównuje wyniki, może uwzględniać Lvl i fortyfikacje.
  
  **4 tryby edycji**
  
  -prowincje
  
  łatwo koloruj mapkę: lewy przycisk do kolorowania, prawy do pobrania koloru z mapki. w menu można wybrać kolor jaśniejszy
    
  -budynki
  
  możesz dodawać łatwo kolorowe ikony budynków, będą one przypisane do tabeli na po kolorze w trybie prowincji oraz jeśli jest droga pod nią.
  ikony zaczynają się z nazwą "b_" w folderze icons. prawy przycisk wymazuje

  -drogi

  możesz rysować drogi w 4 grubościach i dowolnym kolorze, ale do tabeli liczy się tylko kolor szary. prawym przyciskiem wymazuje

  -armie

  rysuj ikony w kolorze państwa. zaliczenie do tabeli dodaje na podstawie koloru środkowego piksela.
  inony zaczynają się nazwą "a_" i powinny mieć mieć biały kolor, najlepiej w ogóle jakby były czarno-białe.



### Opcje uruchamiania:

--load - wczytuje ścieżkę zapisanej mapki w .zip

--dark - tryb ciemny aplikacji

--no_roads - wyłącza konieczność połączenia budynku drogami

--battle - tryb bitew w konsoli

Flagi i komendy dla trybu battle:

>  --gui - zaawanowana modyfikacja armii
> 
>    -r - zwraca losowe armie
> 
>    -f - umożliwia uzględnienie fortyfikacji
> 
>    -lvl  - umożliwia modyfikację lvl
> 
>    -e - printuje szczegóły
>
>   [państwo1] vs [państwo2] - wyświetli w podsumowaniu nazwy zamiast "agresor" "obrońca"
>

> 

### Dodawanie nowych map:
uruchom aplikację z gałęzi dupa i stwórz plik zip z obrazem o nazwie base_image.png

### Modyfigacje Kodu
Masz dostępny szablon dla trybu. 
tryby inicjujemy w controllers/map_controller/mode_manager.py. 
zmienianie już istniejących trybów powinno być w miarę bezbolesne.
