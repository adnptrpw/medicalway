import Head from "next/head";
import Image from "next/image";
import styles from "../styles/Home.module.css";

import {
  Box,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
} from "@chakra-ui/react";
import { SearchIcon } from "@chakra-ui/icons";

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Medicalway</title>
        <meta name="description" content="Home" />
        <link rel="icon" href="/logo.svg" />
      </Head>

      <main className={styles.main}>
          <Box mb={8}>
            <img src="/logo-text.svg" alt="Medicalway"></img>
          </Box>

          <InputGroup width={1000}>
            <InputLeftElement
              pointerEvents="none"
              children={<SearchIcon color="gray.300" />}
            />
            <Input placeholder="Search" borderRadius={1000} />
          </InputGroup>

          <Button colorScheme="blue" mt={4} borderRadius={1000} width={150}>
            Search
          </Button>
      </main>
    </div>
  );
}