"""
Referensi:
[1] https://www.nltk.org/api/nltk.stem.snowball.html
"""

import os
import pickle
import contextlib
import heapq
import time
import math

import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

from string import punctuation

from index import InvertedIndexReader, InvertedIndexWriter
from util import IdMap, sorted_merge_posts_and_tfs
from compression import StandardPostings, VBEPostings
from tqdm import tqdm

class BSBIIndex:
    """
    Attributes
    ----------
    term_id_map(IdMap): Untuk mapping terms ke termIDs
    doc_id_map(IdMap): Untuk mapping relative paths dari dokumen (misal,
                    /collection/0/gamma.txt) to docIDs
    data_dir(str): Path ke data
    output_dir(str): Path ke output index files
    postings_encoding: Lihat di compression.py, kandidatnya adalah StandardPostings,
                    VBEPostings, dsb.
    index_name(str): Nama dari file yang berisi inverted index
    """
    def __init__(self, data_dir, output_dir, postings_encoding, index_name = "main_index"):
        self.term_id_map = IdMap()
        self.doc_id_map = IdMap()
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.index_name = index_name
        self.postings_encoding = postings_encoding

        # Untuk menyimpan nama-nama file dari semua intermediate inverted index
        self.intermediate_indices = []

    def save(self):
        """Menyimpan doc_id_map and term_id_map ke output directory via pickle"""

        with open(os.path.join(self.output_dir, 'terms.dict'), 'wb') as f:
            pickle.dump(self.term_id_map, f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'wb') as f:
            pickle.dump(self.doc_id_map, f)

    def load(self):
        """Memuat doc_id_map and term_id_map dari output directory"""

        with open(os.path.join(self.output_dir, 'terms.dict'), 'rb') as f:
            self.term_id_map = pickle.load(f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'rb') as f:
            self.doc_id_map = pickle.load(f)

    def parse_block(self, block_dir_relative):
        """
        Lakukan parsing terhadap text file sehingga menjadi sequence of
        <termID, docID> pairs.

        Gunakan tools available untuk Stemming Bahasa Inggris

        JANGAN LUPA BUANG STOPWORDS!

        Untuk "sentence segmentation" dan "tokenization", bisa menggunakan
        regex atau boleh juga menggunakan tools lain yang berbasis machine
        learning.

        Parameters
        ----------
        block_dir_relative : str
            Relative Path ke directory yang mengandung text files untuk sebuah block.

            CATAT bahwa satu folder di collection dianggap merepresentasikan satu block.
            Konsep block di soal tugas ini berbeda dengan konsep block yang terkait
            dengan operating systems.

        Returns
        -------
        List[Tuple[Int, Int]]
            Returns all the td_pairs extracted from the block
            Mengembalikan semua pasangan <termID, docID> dari sebuah block (dalam hal
            ini sebuah sub-direktori di dalam folder collection)

        Harus menggunakan self.term_id_map dan self.doc_id_map untuk mendapatkan
        termIDs dan docIDs. Dua variable ini harus 'persist' untuk semua pemanggilan
        parse_block(...).
        """
        stemmer = SnowballStemmer("english")
        stop_words = stopwords.words('english')
        block_path = os.path.join(self.data_dir, block_dir_relative)

        terms_pairs = []

        for root, dirs, files in os.walk(block_path):
            for docs in files:
                current_doc_id = self.doc_id_map[docs]
                docs_path = os.path.join(block_path, docs)
                with open(docs_path, "r") as f:
                    tokenized_words = word_tokenize(f.read())
                    stemmed_words = [stemmer.stem(word) for word in tokenized_words]

                    cleaned_tokens = []
                    for token in stemmed_words:
                        if (token not in stop_words) and (token not in punctuation):
                            cleaned_tokens.append(token)

                    for t in cleaned_tokens:
                        current_term_id = self.term_id_map[t]
                        terms_pairs.append((current_term_id, current_doc_id))

        return terms_pairs

    def invert_write(self, td_pairs, index):
        """
        Melakukan inversion td_pairs (list of <termID, docID> pairs) dan
        menyimpan mereka ke index. Disini diterapkan konsep BSBI dimana 
        hanya di-mantain satu dictionary besar untuk keseluruhan block.
        Namun dalam teknik penyimpanannya digunakan srategi dari SPIMI
        yaitu penggunaan struktur data hashtable (dalam Python bisa
        berupa Dictionary)

        ASUMSI: td_pairs CUKUP di memori

        Di Tugas Pemrograman 1, kita hanya menambahkan term dan
        juga list of sorted Doc IDs. Sekarang di Tugas Pemrograman 2,
        kita juga perlu tambahkan list of TF.

        Parameters
        ----------
        td_pairs: List[Tuple[Int, Int]]
            List of termID-docID pairs
        index: InvertedIndexWriter
            Inverted index pada disk (file) yang terkait dengan suatu "block"
        """
        term_dict = {}
        for term_id, doc_id in td_pairs:
            term_dict.setdefault(term_id, {})
            term_dict[term_id].setdefault(doc_id, 0)
            term_dict[term_id][doc_id] += 1
        for term_id in sorted(term_dict.keys()):
            sorted_df_pairs = dict(sorted(term_dict[term_id].items()))
            sorted_terms = list(sorted_df_pairs.keys())
            sorted_tf = list(sorted_df_pairs.values())
            index.append(term_id, sorted_terms, sorted_tf)

    def merge(self, indices, merged_index):
        """
        Lakukan merging ke semua intermediate inverted indices menjadi
        sebuah single index.

        Ini adalah bagian yang melakukan EXTERNAL MERGE SORT

        Gunakan fungsi orted_merge_posts_and_tfs(..) di modul util

        Parameters
        ----------
        indices: List[InvertedIndexReader]
            A list of intermediate InvertedIndexReader objects, masing-masing
            merepresentasikan sebuah intermediate inveted index yang iterable
            di sebuah block.

        merged_index: InvertedIndexWriter
            Instance InvertedIndexWriter object yang merupakan hasil merging dari
            semua intermediate InvertedIndexWriter objects.
        """
        # kode berikut mengasumsikan minimal ada 1 term
        merged_iter = heapq.merge(*indices, key = lambda x: x[0])
        curr, postings, tf_list = next(merged_iter) # first item
        for t, postings_, tf_list_ in merged_iter: # from the second item
            if t == curr:
                zip_p_tf = sorted_merge_posts_and_tfs(list(zip(postings, tf_list)), \
                                                      list(zip(postings_, tf_list_)))
                postings = [doc_id for (doc_id, _) in zip_p_tf]
                tf_list = [tf for (_, tf) in zip_p_tf]
            else:
                merged_index.append(curr, postings, tf_list)
                curr, postings, tf_list = t, postings_, tf_list_
        merged_index.append(curr, postings, tf_list)

    def retrieve_tfidf(self, query, k = 10):
        """
        Melakukan Ranked Retrieval dengan skema TaaT (Term-at-a-Time).
        Method akan mengembalikan top-K retrieval results.

        w(t, D) = (1 + log tf(t, D))       jika tf(t, D) > 0
                = 0                        jika sebaliknya

        w(t, Q) = IDF = log (N / df(t))

        Score = untuk setiap term di query, akumulasikan w(t, Q) * w(t, D).
                (tidak perlu dinormalisasi dengan panjang dokumen)

        catatan: 
            1. informasi DF(t) ada di dictionary postings_dict pada merged index
            2. informasi TF(t, D) ada di tf_li
            3. informasi N bisa didapat dari doc_length pada merged index, len(doc_length)

        Parameters
        ----------
        query: str
            Query tokens yang dipisahkan oleh spasi

            contoh: Query "universitas indonesia depok" artinya ada
            tiga terms: universitas, indonesia, dan depok

        Result
        ------
        List[(int, str)]
            List of tuple: elemen pertama adalah score similarity, dan yang
            kedua adalah nama dokumen.
            Daftar Top-K dokumen terurut mengecil BERDASARKAN SKOR.

        JANGAN LEMPAR ERROR/EXCEPTION untuk terms yang TIDAK ADA di collection.

        """
        # Load term_id_map dan doc_id_map
        self.load()

        # Struktur: { doc_name: score }
        scores = {}

        tokenized_query = word_tokenize(query)

        stemmer = SnowballStemmer("english")
        stemmed_query = [stemmer.stem(word) for word in tokenized_query]

        stop_words = stopwords.words('english')
        cleaned_query = []
        for q in stemmed_query:
            if (q not in stop_words) and (q not in punctuation):
                cleaned_query.append(q)

        with InvertedIndexReader(self.index_name, self.postings_encoding, directory=self.output_dir) as index:
            for word in cleaned_query:
                if word not in self.term_id_map:
                    continue
                term_id = self.term_id_map[word]

                # IDF = log (N / df(t))
                idf_score = math.log(len(index.doc_length) / index.postings_dict[term_id][1])
                postings_list = index.get_postings_list(term_id)
                for i in range(len(postings_list[0])):
                    doc_id, tf = postings_list[0][i], postings_list[1][i]
                    doc_name = self.doc_id_map[doc_id]
                    # TF = 1 + log(tf(t, D))
                    # Kondisi tf > 0 tidak diperlukan karena dipastikan saat pembuatan postings_list
                    tf_score = 1 + math.log(tf)

                    if doc_name not in scores:
                        scores[doc_name] = 0

                    scores[doc_name] = scores[doc_name] + (idf_score * tf_score)

        # Sort berdasarkan nilai score
        return [(doc_name, score) for (score, doc_name) in sorted(scores.items(), key=lambda value: value[1], reverse=True)[:k]]

    def retrieve_bm25(self, query, k = 10, k1 = 1.5, b = 0.75):
        """
        Melakukan Ranked Retrieval dengan skema TaaT (Term-at-a-Time).
        Method akan mengembalikan top-K retrieval results.

        w(t, D) = (1 + log tf(t, D))       jika tf(t, D) > 0
                = 0                        jika sebaliknya

        w(t, Q) = IDF = log (N / df(t))

        Score = untuk setiap term di query, akumulasikan w(t, Q) * w(t, D).
                (tidak perlu dinormalisasi dengan panjang dokumen)

        catatan:
            1. informasi DF(t) ada di dictionary postings_dict pada merged index
            2. informasi TF(t, D) ada di tf_li
            3. informasi N bisa didapat dari doc_length pada merged index, len(doc_length)

        Parameters
        ----------
        query: str
            Query tokens yang dipisahkan oleh spasi

            contoh: Query "universitas indonesia depok" artinya ada
            tiga terms: universitas, indonesia, dan depok

        Result
        ------
        List[(int, str)]
            List of tuple: elemen pertama adalah score similarity, dan yang
            kedua adalah nama dokumen.
            Daftar Top-K dokumen terurut mengecil BERDASARKAN SKOR.

        JANGAN LEMPAR ERROR/EXCEPTION untuk terms yang TIDAK ADA di collection.

        """
        # Load term_id_map dan doc_id_map
        self.load()

        # Struktur: { doc_name: score }
        scores = {}
        tokenized_query = word_tokenize(query)

        stemmer = SnowballStemmer("english")
        stemmed_query = [stemmer.stem(word) for word in tokenized_query]

        stop_words = stopwords.words('english')
        cleaned_query = []
        for q in stemmed_query:
            if (q not in stop_words) and (q not in punctuation):
                cleaned_query.append(q)

        with InvertedIndexReader(self.index_name, self.postings_encoding, directory=self.output_dir) as index:
            for word in cleaned_query:
                if word not in self.term_id_map: continue
                term_id = self.term_id_map[word]

                # IDF = log (N / df(t))
                idf_score = math.log(len(index.doc_length) / index.postings_dict[term_id][1])

                postings_list = index.get_postings_list(term_id)
                for i in range(len(postings_list[0])):
                    doc_id, tf = postings_list[0][i], postings_list[1][i]
                    doc_name = self.doc_id_map[doc_id]

                    # Formula Okapi BM25
                    bm25_score = idf_score
                    bm25_score *= (tf * (k1 + 1))
                    bm25_score /= (k1 * ((1 - b) + b * (index.doc_length[doc_id] / index.avg_doc_length)) + tf)

                    if doc_name not in scores:
                        scores[doc_name] = 0

                    scores[doc_name] = scores[doc_name] + bm25_score

        # Sort berdasarkan nilai score, ubah urutan nama dan skor
        return [(doc_name, score) for (score, doc_name) in sorted(scores.items(), key=lambda value: value[1], reverse=True)[:k]]

    def index(self):
        """
        Base indexing code
        BAGIAN UTAMA untuk melakukan Indexing dengan skema BSBI (blocked-sort
        based indexing)

        Method ini scan terhadap semua data di collection, memanggil parse_block
        untuk parsing dokumen dan memanggil invert_write yang melakukan inversion
        di setiap block dan menyimpannya ke index yang baru.
        """
        # loop untuk setiap sub-directory di dalam folder collection (setiap block)
        for block_dir_relative in tqdm(sorted(next(os.walk(self.data_dir))[1])):
            td_pairs = self.parse_block(block_dir_relative)
            index_id = 'intermediate_index_'+block_dir_relative
            self.intermediate_indices.append(index_id)
            with InvertedIndexWriter(index_id, self.postings_encoding, directory = self.output_dir) as index:
                self.invert_write(td_pairs, index)
                td_pairs = None
    
        self.save()

        with InvertedIndexWriter(self.index_name, self.postings_encoding, directory = self.output_dir) as merged_index:
            with contextlib.ExitStack() as stack:
                indices = [stack.enter_context(InvertedIndexReader(index_id, self.postings_encoding, directory=self.output_dir))
                               for index_id in self.intermediate_indices]
                self.merge(indices, merged_index)


if __name__ == "__main__":
    nltk.download('punkt')
    nltk.download('stopwords')

    punctuation = list(punctuation)

    BSBI_instance = BSBIIndex(data_dir = 'collection', \
                              postings_encoding = VBEPostings, \
                              output_dir = 'index')
    BSBI_instance.index() # memulai indexing!
