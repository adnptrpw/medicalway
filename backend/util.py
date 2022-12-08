class IdMap:
    """
    Ingat kembali di kuliah, bahwa secara praktis, sebuah dokumen dan
    sebuah term akan direpresentasikan sebagai sebuah integer. Oleh
    karena itu, kita perlu maintain mapping antara string term (atau
    dokumen) ke integer yang bersesuaian, dan sebaliknya. Kelas IdMap ini
    akan melakukan hal tersebut.
    """

    def __init__(self):
        """
        Mapping dari string (term atau nama dokumen) ke id disimpan dalam
        python's dictionary; cukup efisien. Mapping sebaliknya disimpan dalam
        python's list.

        contoh:
            str_to_id["halo"] ---> 8
            str_to_id["/collection/dir0/gamma.txt"] ---> 54

            id_to_str[8] ---> "halo"
            id_to_str[54] ---> "/collection/dir0/gamma.txt"
        """
        self.str_to_id = {}
        self.id_to_str = []

    def __len__(self):
        """Mengembalikan banyaknya term (atau dokumen) yang disimpan di IdMap."""
        return len(self.id_to_str)

    def __get_str(self, i):
        """Mengembalikan string yang terasosiasi dengan index i."""
        return self.id_to_str[i]

    def __get_id(self, s):
        """
        Mengembalikan integer id i yang berkorespondensi dengan sebuah string s.
        Jika s tidak ada pada IdMap, lalu assign sebuah integer id baru dan kembalikan
        integer id baru tersebut.
        """
        if s in self.str_to_id:
            return self.str_to_id[s]
        self.str_to_id[s] = len(self.id_to_str)
        self.id_to_str.append(s)
        return self.str_to_id[s]

    def __getitem__(self, key):
        """
        __getitem__(...) adalah special method di Python, yang mengizinkan sebuah
        collection class (seperti IdMap ini) mempunyai mekanisme akses atau
        modifikasi elemen dengan syntax [..] seperti pada list dan dictionary di Python.

        Silakan search informasi ini di Web search engine favorit Anda. Saya mendapatkan
        link berikut:

        https://stackoverflow.com/questions/43627405/understanding-getitem-method

        Jika key adalah integer, gunakan __get_str;
        jika key adalah string, gunakan __get_id
        """
        if type(key) is int:
            return self.__get_str(key)
        elif type(key) is str:
            return self.__get_id(key)
        else:
            raise TypeError
