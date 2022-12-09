import Head from "next/head";
import Image from "next/image";
import Link from "next/link";
import { GetServerSideProps, NextPage } from "next";
import styles from "../../styles/Home.module.css";

import {
  Button,
  Divider,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
  Text
} from "@chakra-ui/react";
import { SearchIcon } from "@chakra-ui/icons";

import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";

const Search: NextPage<{
  querySearch: any;
  serpData: any;
}> = (props) => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState(props.querySearch.query);

  const handleQuery = (e: ChangeEvent<HTMLInputElement>) => {
    const newSearchQuery = e.target.value;
    setSearchQuery(newSearchQuery);
  };

  const searchFunction = async () => {
    if (searchQuery !== "") {
      router.push({ pathname: `/search/${searchQuery}` });
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Search | Medicalway</title>
        <meta name="description" content="Search" />
        <link rel="icon" href="/logo.svg" />
      </Head>

      <main className={styles.search}>
        <Flex>
          <Link href="/" passHref>
            <Image
              src="/logo-text.svg"
              alt="Medicalway"
              width={248}
              height={100}
            />
          </Link>

          <InputGroup width={1000} ml={4}>
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
            ml={4}
            borderRadius={1000}
            width={150}
            type={"submit"}
            onClick={searchFunction}
          >
            Search
          </Button>
        </Flex>

        <Divider mt={3} mb={2} />

        <Stack>
          <Text mb={3}>About {props.serpData.length} results ({props.serpData.duration} seconds)</Text>

          {Object.keys(props.serpData.serp).map((key) => {
            return (
              <Stack>
                <Text>{key}</Text>
                <Text>{props.serpData.serp[key]}</Text>
              </Stack>
            );
          })}
        </Stack>
      </main>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async ({
  params,
  res,
}) => {
  try {
    const result = await fetch(process.env.API + `search?query=${params}`);
    const data = await result.json();

    return {
      props: { querySearch: params, serpData: data },
    };
  } catch {
    res.statusCode = 404;
    return {
      props: {},
    };
  }
};

export default Search;
