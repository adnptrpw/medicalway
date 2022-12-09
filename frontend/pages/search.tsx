import Head from "next/head";
import Image from "next/image";
import styles from "../styles/Home.module.css";

import {
  Box,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
} from "@chakra-ui/react";
import { SearchIcon } from "@chakra-ui/icons";

import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";

const Search = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState<string>("");

  const handleQuery = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const searchFunction = async () => {
    if (searchQuery !== "") {
      const response = await fetch(
        `https://asia-southeast2-medicalway-ir.cloudfunctions.net/search?query=${searchQuery}`
      );
      const data = await response.json();
      console.log(data);
      router.push({ pathname: "/search", query: { q: searchQuery, d: data } });
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Medicalway</title>
        <meta name="description" content="Home" />
        <link rel="icon" href="/logo.svg" />
      </Head>

      <main className={styles.main}>
        <Box mb={8}>
          <Image
            src="/logo-text.svg"
            alt="Medicalway"
            width={419}
            height={100}
          />
        </Box>

        <InputGroup width={1000}>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder="Search"
            borderRadius={1000}
            value={searchQuery}
            onChange={handleQuery}
          />
        </InputGroup>

        <Button
          colorScheme="blue"
          mt={4}
          borderRadius={1000}
          width={150}
          type={"submit"}
          onClick={searchFunction}
        >
          Search
        </Button>
      </main>
    </div>
  );
};

export default Search;
